from dataclasses import dataclass
from pathlib import Path
import re
import pdfplumber

from data.classes import AanvraagInfo, Bedrijf, StudentInfo 

class PDFReaderException(Exception): pass
NOTFOUND = 'NOT FOUND'

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

class NewAanvraagReaderFromPDF:
    def __init__(self, pdf_file: str):
        self.aanvraag = self.read_pdf(pdf_file)
        self.filename = pdf_file
    def __str__(self):
        return f'file:"{self.filename}" aanvraag: "{str(self.aanvraag)}"'
    def read_pdf(self, pdf_file: str)->AanvraagInfo:
        with pdfplumber.open(pdf_file) as pdf:
            if (n := len(pdf.pages)) < 3:
                raise PDFReaderException(f"Verwacht meer pagina's dan {n} in document")
            aanvraag_data = _AanvraagData()
            try:
                tables = self.__init_tables(pdf)
                self.__parse_main_data(tables[0], aanvraag_data)
                self.__parse_title(tables[1], aanvraag_data)
                return self.__convert_data(aanvraag_data)
            except Exception as E:
                raise PDFReaderException(f"Fout bij lezen document: {E}")    
    def __convert_data(self, aanvraag_data: _AanvraagData)->AanvraagInfo:
        if not aanvraag_data.valid():
            return None
        bedrijf = Bedrijf(aanvraag_data.bedrijf)
        student = StudentInfo(aanvraag_data.student, aanvraag_data.studnr, aanvraag_data.telno, aanvraag_data.email)
        return AanvraagInfo(student, bedrijf, aanvraag_data.datum_str, aanvraag_data.titel)
    def __init_tables(self, pdf: pdfplumber.PDF)->list[list[str]]:
        def listify(page):
            return page.extract_text(use_text_flow=True,split_at_punctuation=True).split('\n')
        tables = []
        for page in pdf.pages:
            tables.append(listify(page))
            #note: this works better than the pdf_plumber table extraction methods, it is fairly easy to get the right data this way
        if len(tables) < 3:
            raise PDFReaderException(f'Verwacht 3 of meer tabellen in document ({len(tables)} gevonden)')
        return [tables[0], self.__merge_tables(tables[1:])]
    def __merge_tables(self, tables:list[list[str]])->list[str]:
        def table_merged_text(table: list[str]):
            result = []
            for row in table:
                merged_row = row[0]
                for col in row[1:]:
                    merged_row += col
                result.append(merged_row)
            return result
        result = tables[0]
        for table in tables[1:]:
            result.extend(table)
        return table_merged_text(result)
    def rectify_table(self, table: list[str], field_keys: list[str])->list[str]:
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
        for row, row_text in enumerate(table):
            if skip_until and skip_until >=row:
                if skip_until == row:
                    skip_until = None
                continue
            for key in field_keys:
                if  len(row_text) < len(key) and re.match(row_text, key):
                    n_lines, value = try_find_rest(table[row+1:], key[len(row_text):])
                    if value:
                        result.append(f'{key} {value}')
                        skip_until = row + n_lines+1
            if not skip_until:
                result.append(row_text)
        return result
    def __parse_first_table(self, table: list[str], field_keys: list[str])->dict:
        def find_pattern(table_row: str)->tuple[str,str]:
            for key in field_keys:
                if (m :=re.match(fr'{key}\s+(?P<value>.*)', table_row, flags=re.IGNORECASE)):
                    return (key, m.group('value'))
            return (None, None)
        table = self.rectify_table(table, field_keys)
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
        student_dict_fields = {'Student': 'student', 'Studentnummer': 'studnr', 'Telefoonnummer': 'telno', 'E-mailadres': 'email', 'Bedrijfsnaam': 'bedrijf', 'Datum/revisie': 'datum_str'}
        END_ROW = len(student_dict_fields) + 12 # een beetje langer ivm bedrijfsnaam en sommige aanvragen met "extra" regels
        if  END_ROW >= len(table):
            raise PDFReaderException(f'Fout in parse_main_data ({END_ROW} rijen verwacht): de tabel heeft {len(table)} rijen.')
        table_dict = self.__parse_first_table(table[:END_ROW], student_dict_fields.keys())
        self.__convert_fields(table_dict, student_dict_fields, aanvraag_data)
    def __convert_fields(self, fields_dict:dict, translation_table, aanvraag_data: _AanvraagData):
        for field in translation_table:               
            setattr(aanvraag_data, translation_table[field], fields_dict.get(field, NOTFOUND))    
    def __parse_title(self, table:list[list[str]], aanvraag_data: _AanvraagData)->str:
        #regex because some students somehow lose the '.' characters or renumber the paragraphs, also older versions of the form have different paragraphs and some students do even stranger things
        regex_versies = [{'start':'\d.*\(Voorlopige.*\) Titel van de afstudeeropdracht', 'end':'\d.*Wat is de aanleiding voor de opdracht\?'},
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



testfiles=[r'C:\repos\aapa\DEMO\marie\Marie 123.pdf',
r'C:\repos\aapa\temp2\Keanu-Attema_Afstudeeropdracht_V7[24].pdf',
r'C:\repos\aapa\DEMO\tammo\Afstudeeropdracht_Tammo_Jan_Tamminga ICN.pdf',
r'C:\repos\aapa\temp2\Keanu-Attema_Afstudeeropdracht_V6[7].pdf',
r'C:\repos\aapa\temp2\Aanvraag goedkeuring Beenen afstudeeropdracht 2022-2023[22].pdf',
r'C:\repos\aapa\temp2\Keanu-Attema_Afstudeeropdracht_V3.pdf',
r'C:\repos\aapa\temp2\Kevin Schiphof - 4719409 - Aanvraag stage v2.02.pdf',
r'C:\repos\aapa\temp2\Afstudeeropdracht - Kevin Schiphof - 4719409.pdf',
r'C:\repos\aapa\temp2\2. Beoordeling afstudeeropdracht - v1.docx.pdf',
r'C:\repos\aapa\temp2\Afstudeeropdracht Versie 1 Joop de Graaf.pdf',
r'C:\repos\aapa\temp2\Afstudeeropdracht ATOS V1.pdf',
r'C:\repos\aapa\temp2\Afstudeeropdracht_Jorn_Postma.pdf',
r'C:\repos\aapa\temp2\Beoordeling afstudeeropdracht Switches Chipsoft.pdf',
r'C:\repos\aapa\temp2\aanvraag-gw-v2.pdf',
r'C:\repos\aapa\temp2\afstudeeropdracht_3D_24_jan_2023.pdf',
r'C:\repos\aapa\temp2\Beoordeling aanvraag Keanu Attema(3551821) (Grendel Games B.V.)-1.pdf',
r'C:\repos\aapa\temp2\Keanu-Attema_Afstudeeropdracht_V6[7] hack.pdf',
r'C:\repos\aapa\temp2\Beoordeling aanvraag Yannick Kooistra(3478237) (Dok.Works B.V.)-2.pdf',
r'C:\repos\aapa\temp2\Aanvraag eezzee gaming.pdf',
]

def test_aanvraag(file):
    try:
        aanvraag = NewAanvraagReaderFromPDF(file).aanvraag
        if aanvraag:
            print(aanvraag)
    except Exception as E:
        print(E)


path1= r"C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2"

path2 =r'C:\repos\aapa\temp2'

for file in testfiles[0:5]:
# for file in Path(path1).glob('**/*.pdf'):
    print(file)
    test_aanvraag(file)

