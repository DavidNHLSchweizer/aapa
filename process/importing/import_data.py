from dataclasses import dataclass
from enum import Enum
import re
from pathlib import Path
import tkinter
import pandas as pd
import pdfplumber
import tabula
from process.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.classes import AUTOTIMESTAMP, AanvraagInfo, Bedrijf, FileInfo, FileType, StudentInfo
from general.log import logError, logPrint, logWarning, logInfo
from general.valid_email import is_valid_email, try_extract_email
from PyPDF2 import PdfReader

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class PDFReaderException(Exception): pass
NOTFOUND = 'NOT FOUND'


def count_pdf_pages(file_path):
    with open(file_path, 'rb') as f:
        pdf = PdfReader(f, strict=False)
        return len(pdf.pages)

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

class AanvraagReaderFromPDF:
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



class AanvraagDataImporter(AanvraagProcessor):
    def __ask_titel(self, aanvraag: AanvraagInfo)->str:
        return tkinter.simpledialog.askstring(f'Titel', f'Titel voor {str(aanvraag)}') 
    def process(self, filename: str, preview=False)->AanvraagInfo:
        logPrint(f'Lezen {filename}')
        if (aanvraag := AanvraagReaderFromPDF(filename).aanvraag):
            fileinfo = FileInfo(filename, timestamp=AUTOTIMESTAMP, filetype=FileType.AANVRAAG_PDF)
            if self.is_duplicate(fileinfo):            
                logWarning(f'Duplikaat: {filename}.\nal in database: {str(aanvraag)}')
                return None
            if not is_valid_email(aanvraag.student.email):
                new_email = try_extract_email(aanvraag.student.email, True)
                if new_email:
                    logWarning(f'Aanvraag email is ongeldig ({aanvraag.student.email}), aangepast als {new_email}.')
                    aanvraag.student.email = new_email
                else:
                    logError(f'Aanvraag email is ongeldig: {aanvraag.student.email}')
                    return None
            if not aanvraag.titel:
                aanvraag.titel=self.__ask_titel(aanvraag)
            logInfo(f'--- Start storing imported data from PDF {filename}')
            if not preview:
                self.storage.create_aanvraag(aanvraag, fileinfo) 
                self.aanvragen.append(aanvraag)
                self.storage.commit()
                logInfo(f'--- Succes storing imported data from PDF {filename}')
            logPrint(f'\t{str(aanvraag)}')
            return aanvraag
        return None
    def store_invalid(self, filename):
        self.storage.create_fileinfo(FileInfo(filename, AUTOTIMESTAMP, FileType.INVALID_PDF))
        self.storage.commit()
    def is_duplicate(self, file: FileInfo):
        return (stored:=self.storage.read_fileinfo(file.filename)) is not None and stored.timestamp == file.timestamp

class ImportResult(Enum):
    UNKNOWN  = 0
    IMPORTED = 1
    ERROR    = 2
    ALREADY_IMPORTED = 3
    KNOWN_ERROR = 4
    KNOWN_PDF = 5
    COPIED_FILE = 6

def _import_aanvraag(filename: str, importer: AanvraagDataImporter)->ImportResult:
    def known_import_result(filename)->ImportResult:
        def not_changed(filename, fileinfo):
            return FileInfo.get_timestamp(filename) == fileinfo.timestamp
        if (fileinfo := importer.known_file_info(filename)):
            match fileinfo.filetype:
                case FileType.AANVRAAG_PDF | FileType.COPIED_PDF:
                    if not_changed(filename, fileinfo): 
                        return ImportResult.ALREADY_IMPORTED if fileinfo.filetype == FileType.AANVRAAG_PDF else ImportResult.COPIED_FILE
                    else:
                        return ImportResult.UNKNOWN
                case FileType.GRADED_PDF:
                    return ImportResult.KNOWN_PDF
                case FileType.INVALID_PDF:
                    if not_changed(filename, fileinfo): 
                        return ImportResult.KNOWN_ERROR
                    else:
                        return ImportResult.UNKNOWN
        return ImportResult.UNKNOWN
    try:
        if (result := known_import_result(filename)) == ImportResult.UNKNOWN: 
            if importer.process(filename): 
                return ImportResult.IMPORTED
            else:
                return ImportResult.ERROR
        return result
    except PDFReaderException as E:
        logError(f'Fout bij importeren {filename}:\n\t{E}\n\t{ERRCOMMENT}')        
        importer.store_invalid(filename)
        return ImportResult.ERROR

def report_imports(file_results:dict, new_aanvragen, preview):
    def import_status_str(result):
        match result:
            case ImportResult.IMPORTED: return 'te importeren' if preview else 'geimporteerd'
            case ImportResult.ERROR: return 'kan niet worden geimporteerd' if preview else 'fout bij importeren'
            case ImportResult.ALREADY_IMPORTED: return 'eerder geimporteerd'
            case ImportResult.COPIED_FILE: return 'kopie van aanvraag (eerder geimporteerd)'
            case ImportResult.KNOWN_ERROR: return 'eerder gelezen, kan niet worden geimporteerd'
            case _: return '???'
    def file_str(file,result):
        return f'{file} [{import_status_str(result)}]'
    print('Rapportage import:')
    print('\t---Gelezen bestand(en):---')
    print('\t\t'+ '\n\t\t'.join([file_str(file, result) for file,result in file_results.items()]))
    print('\t--- Nieuwe aanvragen --- :')
    print('\t\t'+'\n\t\t'.join([str(aanvraag) for aanvraag in new_aanvragen]))
    gelezen = 'te lezen' if preview else 'gelezen'
    print(f'\t{len(new_aanvragen)} nieuwe aanvragen {gelezen}.')


def import_directory(directory: str, storage: AAPStorage, recursive = True, preview=False)->tuple[int,int]:
    def _get_pattern(recursive: bool):
        return '**/*.pdf' if recursive else '*.pdf'
    min_id = storage.max_aanvraag_id() + 1
    if not Path(directory).is_dir():
        logWarning(f'Map {directory} bestaat niet. Afbreken.')
        return (min_id,min_id)
    logPrint(f'Start import van map  {directory}...')
    if not preview:
        storage.add_file_root(str(directory))
    importer = AanvraagDataImporter(storage)
    file_results = {}
    for file in Path(directory).glob(_get_pattern(recursive)):
        import_result = _import_aanvraag(file, importer)
        file_results[file] = import_result
    max_id = storage.max_aanvraag_id()    
    report_imports(file_results, importer.filtered_aanvragen(lambda x: x.id >= min_id), preview=preview)
    logPrint(f'...Import afgerond')
    return (min_id, max_id)
        