from dataclasses import dataclass
import re
import pdfplumber
from data.classes import AanvraagInfo, Bedrijf, StudentInfo
from general.config import IntValueConvertor, config

def init_config():
    config.register('pdf_read', 'x_tolerance', IntValueConvertor)
    config.init('pdf_read', 'x_tolerance', 3)
init_config()


ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class PDFReaderException(Exception): pass
NOTFOUND = 'NOT FOUND'

class PDFtoTablesReader:
    def __init__(self, pdf_file: str, expected_tables=0, expected_pages=0):
        self.tables = self.read_tables_from_pdf(pdf_file, expected_tables=expected_tables, expected_pages=expected_pages)
        self.filename = pdf_file
    def read_tables_from_pdf(self, pdf_file: str, expected_pages=0, expected_tables=0)->list[list[str]]:
        with pdfplumber.open(pdf_file) as pdf:
            if (n := len(pdf.pages)) < expected_pages:
                raise PDFReaderException(f"Verwacht minimaal {expected_pages} pagina's. {n} pagina's in document.")
            try:
                return self.__init_tables(pdf, expected_tables=expected_tables)
            except Exception as E:
                raise PDFReaderException(f"Fout bij lezen document: {E}")    
    def __init_tables(self, pdf: pdfplumber.PDF, expected_tables=0)->list[list[str]]:
        tables = []
        for page in pdf.pages:
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
    student_dict_fields = {'Student': 'student', 'Studentnummer': 'studnr', 'Telefoonnummer': 'telno', 'E-mailadres': 'email', 'Bedrijfsnaam': 'bedrijf', 'Datum/revisie': 'datum_str'}
    END_ROW = len(student_dict_fields) + 12 # een beetje langer ivm bedrijfsnaam en sommige aanvragen met "extra" regels
    def __init__(self,pdf_file: str):
        super().__init__(pdf_file, expected_pages=3, expected_tables=3)
        self.tables = [self.rectify_table(self.tables[0], PDFaanvraagReader.END_ROW, PDFaanvraagReader.student_dict_fields.keys()), self.all_lines(first_table = 1)]   
    def rectify_table(self, table: list[str], rows_to_rectify: int, field_keys: list[str])->list[str]:
        # some students manage to cause table keys (e.g. Studentnummer) to split over multiple lines (Studentnumme\nr)
        # this method tries to rectify this by rejoining the keys and assuming that the actual values (column 2) are in between
        def try_find_rest(table, rest_key):
            value = ''
            for n, row_text in enumerate(table):
                if row_text != rest_key:
                    value += row_text
                else:
                    break
            return n, value        
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
    student = ''
    studnr = ''
    telno = ''
    email = ''
    bedrijf = ''
    titel = ''
    def __str__(self):
        return f'student: {self.student} ({self.studnr})  telno: {self.telno}  email: {self.email}\nbedrijf: {self.bedrijf}  titel: {self.titel}  datum_str: {self.datum_str}'
    def valid(self)->bool:
        if not self.student or not self.bedrijf  or not self.email:
            return False
        if self.student == NOTFOUND or self.bedrijf == NOTFOUND or self.email == NOTFOUND:
            return False      
        return True

class AanvraagReaderFromPDF(PDFaanvraagReader):
    def __init__(self, pdf_file: str):
        super().__init__(pdf_file)
        self.aanvraag = self.get_aanvraag()
    def __str__(self):
        return f'file:"{self.filename}" aanvraag: "{str(self.aanvraag)}"'
    def get_aanvraag(self)->AanvraagInfo:            
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
    def __convert_data(self, aanvraag_data: _AanvraagData)->AanvraagInfo:
        if not aanvraag_data.valid():
            return None
        bedrijf = Bedrijf(aanvraag_data.bedrijf)
        student = StudentInfo(aanvraag_data.student, aanvraag_data.studnr, aanvraag_data.telno, aanvraag_data.email)
        return AanvraagInfo(student, bedrijf, aanvraag_data.datum_str, aanvraag_data.titel)
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
    def __parse_title(self, table:list[str], aanvraag_data: _AanvraagData)->str:
        #regex because some students somehow lose the '.' characters or renumber the paragraphs, also older versions of the form have different paragraphs and some students do even stranger things
        regex_versies = [{'start':'\d.*\(\s*Voorlopige.*\) Titel van de afstudeeropdracht', 'end':'\d.*Wat is de aanleiding voor de opdracht\s*\?'},
                         {'start':'\d.*Titel van de afstudeeropdracht', 'end': '\d.*Korte omschrijving van de opdracht.*'},                        
                         {'start':'.*Titel van de afstudeeropdracht', 'end': '.*Korte omschrijving van de opdracht.*'},                        
                        ]
        for versie in regex_versies:
            aanvraag_data.titel = ' '.join(self.__get_strings_from_table(table, versie['start'], versie['end'])).strip()
            if aanvraag_data.titel:
                break
        return aanvraag_data.titel
    def __get_strings_from_table(self, table: list[str], start_paragraph_regex:str, end_paragraph_regex:str)->list[str]:
        row1, row2 = self.__find_range_from_table(table, start_paragraph_regex, end_paragraph_regex, must_find_both=True)
        result = []
        for row in range(row1, row2-1):
            result.append(table[row])
        return result
    def __find_range_from_table(self, table: list[str], start_paragraph_regex:str, end_paragraph_regex:str, must_find_both = False, ignore_case=False)->tuple[int,int]:
        def row_matches(table, row, pattern:re.Pattern):
            flags = re.IGNORECASE if ignore_case else 0
            if isinstance(table[row], str):
                return pattern.match(table[row], flags) is not None
            elif isinstance(table[row], list):
                return pattern.match(table[row][0], flags) is not None
            else:
                return False
        def find_pattern(regex, row0):
            if not regex:
                return row0
            else:
                row = row0
                pattern = re.compile(regex)
                while row < len(table) and not row_matches(table, row, pattern):
                    row+=1 
                return min(row + 1, len(table))
        row1 = find_pattern(start_paragraph_regex, 0)
        if row1 == len(table) and not must_find_both:
            row1 = 0
        row2 = find_pattern(end_paragraph_regex, row1)
        if row2 == len(table):
            return (1, 0)
        else:
            return (row1,row2)
