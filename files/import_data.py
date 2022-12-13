from dataclasses import dataclass
import datetime
import datetime
import re
from pathlib import Path
import pandas as pd
import tabula
from data.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.aanvraag_info import AUTOTIMESTAMP, AanvraagInfo, Bedrijf, FileInfo, FileType, StudentInfo
from general.log import logError, logPrint, logWarn
from general.valid_email import is_valid_email, try_extract_email

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class PDFReaderException(Exception): pass

def nrows(table: pd.DataFrame)->int:
    return table.shape[0]

def get_file_timestamp(timestamp:datetime.datetime, filename: str)->datetime.datetime:
    if timestamp:
        return timestamp
    else:
        return datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime)

@dataclass
class _AanvraagData:
    pdf_file:str = ''
    datum_str = ''
    student = ''
    studnr = ''
    telno = ''
    email = ''
    bedrijf = ''
    titel = ''

class AanvraagReaderFromPDF:
    def __init__(self, pdf_file: str):
        self.aanvraag = self.read_pdf(pdf_file)
        self.filename = pdf_file
    def __str__(self):
        return f'file:"{self.filename}" aanvraag: "{str(self.aanvraag)}"'
    def read_pdf(self, pdf_file: str)->AanvraagInfo:
        aanvraag_data = _AanvraagData(pdf_file=pdf_file)
        tables = tabula.read_pdf(pdf_file,pages='all')
        self._parse_main_data(tables[0], aanvraag_data)
        self._parse_title(tables[2], aanvraag_data)
        return self.__convert_data(aanvraag_data)
    def __convert_data(self, aanvraag_data: _AanvraagData)->AanvraagInfo:
        fileinfo = FileInfo(aanvraag_data.pdf_file, AUTOTIMESTAMP, FileType.AANVRAAG_PDF)
        bedrijf = Bedrijf(aanvraag_data.bedrijf)
        student = StudentInfo(aanvraag_data.student, aanvraag_data.studnr, aanvraag_data.telno, aanvraag_data.email)
        return AanvraagInfo(fileinfo, student, bedrijf, aanvraag_data.datum_str, aanvraag_data.titel)
    def __convert_fields(self, fields_dict:dict, translation_table, aanvraag_data: _AanvraagData):
        for field in translation_table:            
            setattr(aanvraag_data, translation_table[field], fields_dict.get(field, 'NOT FOUND'))
    def __parse_table(self, table: pd.DataFrame, start_row, end_row, translation_table, aanvraag_data: _AanvraagData):
        table_dict = {}
        if start_row >= nrows(table) or end_row >= nrows(table):
            raise PDFReaderException(f'Fout in parse_table ({start_row}, {end_row}): de tabel heeft {nrows(table)} rijen.\n{ERRCOMMENT}.')
        for row in range(start_row, end_row):
            table_dict[table.values[row][0]] = table.values[row][1]
        self.__convert_fields(table_dict, translation_table, aanvraag_data)
    def __rectify_table(self, table, row0, row1):
        #necessary because some students somehow introduce \r characters in the table first column
        for row in range(row0, row1):
            if isinstance(table.values[row][0], str): #sometimes there is an empty cell that is parsed by tabula as a float NAN
                table.values[row][0] = table.values[row][0].replace('\r', '')
    def _parse_main_data(self, table: pd.DataFrame, aanvraag_data: _AanvraagData):        
        student_dict_fields = {'Datum/revisie': 'datum_str', 'Student': 'student', 'Studentnummer': 'studnr', 'Telefoonnummer': 'telno', 'E-mailadres': 'email', 'Bedrijfsnaam': 'bedrijf'}
        student_dict_len  = len(student_dict_fields) + 5 # een beetje langer ivm bedrijfsnaam
        self.__rectify_table(table, 0, student_dict_len)
        self.__parse_table(table, 0, student_dict_len, student_dict_fields, aanvraag_data)
    def _parse_title(self, table: pd.DataFrame, aanvraag_data: _AanvraagData)->str:
        #regex because some students somehow lose the '.' characters or renumber the paragraphs
        start_paragraph  = '\d.*\(Voorlopige, maar beschrijvende\) Titel van de afstudeeropdracht'
        end_paragraph    = '\d.*Wat is de aanleiding voor de opdracht\?'         
        aanvraag_data.titel = ' '.join(self.__get_strings_from_table(table, start_paragraph, end_paragraph))
    def __get_strings_from_table(self, table:pd.DataFrame, start_paragraph_regex:str, end_paragraph_regex:str)->list[str]:
        def row_matches(table, row, pattern:re.Pattern):
            if isinstance(table.values[row][0], str):
                return pattern.match(table.values[row][0]) is not None
            else:
                return False
        result = []
        row = 0
        start_pattern = re.compile(start_paragraph_regex)
        while row < nrows(table) and not row_matches(table, row, start_pattern):
            row+=1
        row+=1
        end_pattern = re.compile(end_paragraph_regex)
        while row < nrows(table) and not row_matches(table, row, end_pattern):
            result.append(table.values[row][0])
            row+=1
        return result

class AanvraagDataImporter(AanvraagProcessor):
    def process(self, filename: str)->AanvraagInfo:
        if (aanvraag := AanvraagReaderFromPDF(filename).aanvraag):
            if self.is_duplicate(aanvraag):            
                logWarn(f'Duplicate file: {filename}.\nAlready imported {str(aanvraag)}')
                return None
            if not is_valid_email(aanvraag.student.email):
                new_email = try_extract_email(aanvraag.student.email, True)
                if new_email:
                    logWarn(f'Aanvraag email not valid ({aanvraag.student.email}), corrected to {new_email}.')
                    aanvraag.student.email = new_email
                else:
                    logError(f'Aanvraag email not valid: {aanvraag.student.email}')
                    return None
            if not aanvraag.valid():
                logError(f'Aanvraag not valid: {aanvraag}')
                return None
            self.storage.create_aanvraag(aanvraag) 
            self.aanvragen.append(aanvraag)
            logPrint(aanvraag)
            return aanvraag
        return None
    def is_duplicate(self, aanvraag: AanvraagInfo):
        for a in self.aanvragen:
            if a == aanvraag:
                return True
        return False
        
def _import_aanvraag(filename: str, importer: AanvraagDataImporter):
    try:
        logPrint(f'*** IMPORTING {filename}')
        if importer.process(filename):            
            importer.storage.commit()
    except Exception as E:
        logError(f'Error importing {filename}: {E}\n{ERRCOMMENT}')        

def import_directory(directory: str, storage: AAPStorage)->tuple[int,int]:
    min_id = storage.max_aanvraag_id() + 1
    logPrint(f'Start importing from {directory}...')
    importer = AanvraagDataImporter(storage)
    for file in Path(directory).glob('*.pdf'):
        _import_aanvraag(file, importer)
    max_id = storage.max_aanvraag_id()    
    logPrint(f'...Import ready')
    return (min_id, max_id)
        