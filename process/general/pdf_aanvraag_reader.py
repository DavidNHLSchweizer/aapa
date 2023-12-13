from dataclasses import dataclass
import re
import pdfplumber
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File
from data.classes.studenten import Student
from general.config import  IntValueConvertor, ListValueConvertor, ValueConvertor, config
from general.log import log_debug

class TitleRegexConvertor(ValueConvertor):
# De titel vd aanvraag is te bepalen door een pattern aan het begin en eind te matchen.
# (de eigenlijke titel staat daar tussen, met enige complicaties zoals einde van pagina's) 
# Van de patronen zijn er verschillende versies, en de student doet soms ook rare dingen.
# Vandaar deze "omweg" . De TitleRegexConvertor zorgt er voor dat dit in de configfile kan worden gezet 
# en weer teruggelezen zonder verdere tussenstappen
# Voor zover nu bekend zijn alle aanvragen tot nu toe hiermee gedekt.
    PATTERN1 = r'#_RE_START_#'
    PATTERN2 = r'#_RE_END_#'
    PATTERN = f'{PATTERN1}(?P<start>.+){PATTERN2}(?P<end>.+)'
    def get(self, section_key: str, key_value: str, **kwargs)->dict:
        try:
            if (section := self._parser[section_key]) and \
               (match := re.match(TitleRegexConvertor.PATTERN, section.get(key_value, **kwargs), re.IGNORECASE)):
                return {'start': match.group('start'), 'end': match.group('end')} 
        except:
            pass
        return None
    def set(self, section_key: str, key_value: str, value: dict):        
        if (section := self._parser[section_key]) is not None:
            section[key_value] = f'{TitleRegexConvertor.PATTERN1}{value["start"]}{TitleRegexConvertor.PATTERN2}{value["end"]}'

def init_config():
    title_regex_versies = [ {'start':r'\d.*\(\s*Voorlopige.*\) Titel van de afstudeeropdracht', 'end':r'\d.*Wat is de aanleiding voor de opdracht\s*\?'},
                            {'start':r'.*\(\s*Voorlopige.*\) Titel van de afstudeeropdracht', 'end':r'.*Wat is de aanleiding voor de opdracht\s*\?'},
                            {'start':r'\d.*Titel van de afstudeeropdracht', 'end': r'\d.*Korte omschrijving van de opdracht.*'},                        
                            {'start':r'.*Titel van de afstudeeropdracht', 'end': r'.*Korte omschrijving van de opdracht.*'},                        
                          ]
    config.register('pdf_read', 'x_tolerance', IntValueConvertor)
    config.register('pdf_read', 'min_pages', IntValueConvertor)
    config.register('pdf_read', 'expected_tables', IntValueConvertor)
    config.register('pdf_read', 'max_pages', IntValueConvertor)
    config.init('pdf_read', 'x_tolerance', 3)
    config.init('pdf_read', 'min_pages', 3)
    config.init('pdf_read', 'max_pages', 8)
    config.init('pdf_read', 'expected_tables', 3)
    config.register('pdf_read', 'title_regex', ListValueConvertor,  item_convertor=TitleRegexConvertor)     
    config.init('pdf_read', 'title_regex', title_regex_versies)
init_config()

class PDFReaderException(Exception): pass
NOTFOUND = 'NOT FOUND'
TITLE_NOT_FOUND = (1,0)
EMPTY_TITLE = 'Titel niet gevonden'
def is_valid_title(title: str)->bool:
    return title != EMPTY_TITLE

class PDFtoTablesReader:
    def __init__(self, pdf_file: str, expected_tables=0, expected_pages=0, max_pages=0):
        self.filename = pdf_file
        self.tables = self.read_tables_from_pdf(pdf_file, expected_tables=expected_tables, expected_pages=expected_pages, max_pages=max_pages)
    def read_tables_from_pdf(self, pdf_file: str, expected_pages=0, max_pages=0, expected_tables=0)->list[list[str]]:
        with pdfplumber.open(pdf_file) as pdf:
            if (npages := len(pdf.pages)) < expected_pages:
                raise PDFReaderException(f"Verwacht minimaal {expected_pages} pagina's. {npages} pagina's in document.")
            elif npages > max_pages:
                raise PDFReaderException(f"Verwacht maximaal {max_pages} pagina's. {npages} pagina's in document.")
            try:
                return self.__init_tables(pdf, expected_tables=expected_tables)
            except Exception as E:
                raise PDFReaderException(f"Fout bij lezen document: {E}")    
    def __init_tables(self, pdf: pdfplumber.PDF, expected_tables=0)->list[list[str]]:
        tables = []
        for n,page in enumerate(pdf.pages):
            tables.append(page.extract_text(use_text_flow=True,split_at_punctuation=False,x_tolerance=config.get('pdf_read', 'x_tolerance')).split('\n'))
            #note: this works better than the pdf_plumber table extraction methods, it is fairly easy to get the right data this way
        if len(tables) < expected_tables:
            raise PDFReaderException(f'Verwacht {expected_tables} of meer tabellen in document ({len(tables)} gevonden).')
        return tables
    
    def all_lines(self, first_table=None, last_table=None):
        if not first_table:
            first_table = 0
        if not last_table:
            last_table = len(self.tables)
        result = []
        for table in self.tables[first_table:last_table]:
            result.extend(table)
        return result
    
class PDFaanvraagReader(PDFtoTablesReader):
    student_dict_fields = {'Student': 'full_name', 'Studentnummer': 'stud_nr', 'E-mailadres': 'email', 'Bedrijfsnaam': 'bedrijf', 'Datum/revisie': 'datum_str'}
    END_ROW = len(student_dict_fields) + 12 # een beetje langer ivm bedrijfsnaam en sommige aanvragen met "extra" regels
    def __init__(self,pdf_file: str):
        super().__init__(pdf_file, expected_tables=config.get('pdf_read', 'expected_tables'), 
                         expected_pages=config.get('pdf_read', 'min_pages'), 
                         max_pages=config.get('pdf_read', 'max_pages'))
        self.tables = [self.rectify_table(self.tables[0], PDFaanvraagReader.END_ROW, PDFaanvraagReader.student_dict_fields.keys()), self.all_lines(first_table = 1)]   
    def rectify_table(self, table: list[str], rows_to_rectify: int, field_keys: list[str])->list[str]:
        # some students manage to cause table keys (e.g. Studentnummer) to split over multiple lines (Studentnumme\nr)
        # this method tries to rectify this by rejoining the keys and assuming that the actual values (column 2) are in between
        def try_find_rest(table, rest_key):
            value = ''
            if not len(table):
                return 0, None
            for rownr, row_text in enumerate(table):
                if row_text != rest_key:
                    value += row_text
                else:
                    break
            return rownr, value        
        result = []
        skip_until = None
        for row, row_text in enumerate(table[:rows_to_rectify]):
            if skip_until and skip_until >=row:
                if skip_until == row:
                    skip_until = None
                continue
            for key in field_keys:
                #TODO zeproblem is: einddatum) als regular expression werkt niet lekker. Misschien beter gewoon find toepassen?
                if  len(row_text) < len(key) and re.match(row_text, key):
                    n_lines, value = try_find_rest(table[row+1:], key[len(row_text):])
                    if value:
                        result.append(f'{key} {value}')
                        skip_until = row + n_lines+1
            if not skip_until:
                result.append(row_text)
        result.extend(table[rows_to_rectify:])
        return result

@dataclass
class _AanvraagData:
    datum_str = ''
    full_name = ''
    stud_nr = ''
    email = ''
    bedrijf = ''
    titel = ''
    def __str__(self):
        return f'student: {self.full_name} ({self.stud_nr})  email: {self.email}\nbedrijf: {self.bedrijf}  titel: {self.titel}  datum_str: {self.datum_str}'
    def valid(self)->bool:
        if not self.full_name or not self.bedrijf  or not self.email:
            return False
        if self.full_name == NOTFOUND or self.bedrijf == NOTFOUND or self.email == NOTFOUND:
            return False      
        return True
    
def debug_table_report_string(table: list[str], r1:int=None, r2:int=None)->str:
    rr1 = r1 if r1 is not None else 0
    rr2 = r2 if r2 is not None else len(table)
    log_debug(f'{rr1=}, {rr2=}')
    return "\n".join([f'{n}: {line}' for n,line in enumerate(table[rr1:rr2])])

class AanvraagReaderFromPDF(PDFaanvraagReader):
    def read_aanvraag(self)->Aanvraag:            
        aanvraag_data = _AanvraagData()
        try:
            self.__parse_main_data(self.tables[0], aanvraag_data)
            self.__parse_title(self.tables[1], aanvraag_data)
            aanvraag = self.__convert_data(aanvraag_data)
            if not aanvraag:
                raise PDFReaderException(f"Document bevat geen geldige aanvraag")
            return aanvraag
        except Exception as E:
            raise PDFReaderException(f"Fout bij lezen document: {E}")    
    def __convert_data(self, aanvraag_data: _AanvraagData)->Aanvraag:
        if not aanvraag_data.valid():
            return None
        bedrijf = Bedrijf(aanvraag_data.bedrijf)
        student = Student(full_name=aanvraag_data.full_name, stud_nr=aanvraag_data.stud_nr, email=aanvraag_data.email)
        return Aanvraag(student, bedrijf, aanvraag_data.datum_str, aanvraag_data.titel, datum = File.get_timestamp(self.filename),
                        status = Aanvraag.Status.IMPORTED_PDF)
    def __parse_first_table(self, table: list[str], field_keys: list[str])->dict:
        def find_pattern(table_row: str)->tuple[str,str]:
            for key in field_keys:
                if (m :=re.match(fr'{key}\s+(?P<value>.*)', table_row, flags=re.IGNORECASE)):
                    return (key, m.group('value'))
            return (None, None)
        result = {}
        for row in table:
            key, value = find_pattern(row)
            if key and not result.get(key, None): # telefoonnummer is anders verkeerd
                result[key] = value.strip()
        if not result.get('Datum/revisie', None):
            self.__parse_datum_str(table, result, 0)
        return result      
    def __parse_datum_str(self, table, result_dict: dict, col_no: int):
        # supports older version of form as well
        r1, r2 = self.__find_range_from_table(table, r'Studentgegevens.*?$', r'Student.*?$')        
        L = []
        for r in range(r1,r2-1):
            L.append(table[r])
        result_dict['Datum/revisie'] = '/'.join(filter(lambda l: l != '', L))               
    def __parse_main_data(self, table: list[str], aanvraag_data: _AanvraagData):
        table_dict = self.__parse_first_table(table[:PDFaanvraagReader.END_ROW], PDFaanvraagReader.student_dict_fields.keys())
        self.__convert_fields(table_dict, PDFaanvraagReader.student_dict_fields, aanvraag_data)
    def __convert_fields(self, fields_dict:dict, translation_table, aanvraag_data: _AanvraagData):
        for field in translation_table:               
            setattr(aanvraag_data, translation_table[field], fields_dict.get(field, NOTFOUND))    
    def __parse_title(self, table:list[str], aanvraag_data: _AanvraagData):
        title_regex_versies = config.get('pdf_read', 'title_regex')        
        for entry in title_regex_versies:
            table_strings = self.__get_strings_from_table(table, entry['start'], entry['end'])
            if table_strings:
                aanvraag_data.titel = ' '.join(table_strings).strip()
                break
    def __get_strings_from_table(self, table: list[str], start_paragraph_regex:str, end_paragraph_regex:str)->list[str]:
        row1, row2 = self.__find_range_from_table(table, start_paragraph_regex, end_paragraph_regex, must_find_both=True)
        if (row1,row2)==TITLE_NOT_FOUND:
            return None
        result = []
        if row2 == row1+1:
            result.append(EMPTY_TITLE)
        elif row2 > row1 + 1:
            for row in range(row1, row2-1):
                result.append(table[row])
        return result
    def __find_range_from_table(self, table: list[str], start_paragraph_regex:str, end_paragraph_regex:str, must_find_both = False, ignore_case=False)->tuple[int,int]:
        def row_matches(table, row, pattern:re.Pattern):
            if isinstance(table[row], str):
                return pattern.match(table[row]) is not None
            elif isinstance(table[row], list):
                return pattern.match(table[row][0]) is not None
            else:
                return False
        def find_pattern(regex, row0):
            if not regex:
                return row0
            else:
                row = row0
                pattern = re.compile(regex, re.IGNORECASE if ignore_case else 0)
                while row < len(table) and not row_matches(table, row, pattern):
                    row+=1 
                return min(row+1, len(table))
        row1 = find_pattern(start_paragraph_regex, 0)
        if row1 == len(table) and not must_find_both:
            row1 = 0
        row2 = find_pattern(end_paragraph_regex, row1)
        if row2 == len(table):
            return TITLE_NOT_FOUND
        else:
            return (row1,row2)

