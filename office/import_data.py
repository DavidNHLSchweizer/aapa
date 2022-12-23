from dataclasses import dataclass
import datetime
import re
from pathlib import Path
import tkinter
import numpy as np
import pandas as pd
import tabula
from data.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.aanvraag_info import AUTOTIMESTAMP, AanvraagInfo, Bedrijf, FileInfo, FileType, StudentInfo
from general.log import logError, logPrint, logWarn, logInfo
from general.valid_email import is_valid_email, try_extract_email

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class PDFReaderException(Exception): pass
NOTFOUND = 'NOT FOUND'

def nrows(table: pd.DataFrame)->int:
    return table.shape[0]
def ncols(table: pd.DataFrame)->int:
    return table.shape[1]

@dataclass
class _AanvraagData:
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
        aanvraag_data = _AanvraagData()
        try:
            # tables = tabula.read_pdf(pdf_file,pages=list(range(1,4)),multiple_tables=True,area=[70,70,570,790])
            tables = tabula.read_pdf(pdf_file,pages=list(range(1,4)))
        except Exception as E:
            raise PDFReaderException(f"Verwacht meer pagina's in document: {E}")
        if len(tables) < 3:
            raise PDFReaderException(f'Verwacht 3 of meer tabellen in document ({len(tables)}')
        tables[0].fillna(value='', inplace=True) #found some nan some times, just remove those
        self._parse_main_data(tables[0], aanvraag_data)
        # tables[1].fillna(value='', inplace=True) #found some nan some times, just remove those
        #TODO Kevin Schiphof stukje tabel wordt niet gedetecteerd. Negeren voor nu.

        tables[2].fillna(value='', inplace=True) #found some nan some times, just remove those
        self.__parse_title(tables[2], aanvraag_data)
        return self.__convert_data(aanvraag_data)
    def __convert_data(self, aanvraag_data: _AanvraagData)->AanvraagInfo:
        bedrijf = Bedrijf(aanvraag_data.bedrijf)
        student = StudentInfo(aanvraag_data.student, aanvraag_data.studnr, aanvraag_data.telno, aanvraag_data.email)
        return AanvraagInfo(student, bedrijf, aanvraag_data.datum_str, aanvraag_data.titel)
    def __convert_fields(self, fields_dict:dict, translation_table, aanvraag_data: _AanvraagData):
        for field in translation_table:       
            setattr(aanvraag_data, translation_table[field], fields_dict.get(field, NOTFOUND))
    def __parse_table(self, table: pd.DataFrame, start_row, end_row, translation_table, aanvraag_data: _AanvraagData):
        table_dict = {}
        if start_row >= nrows(table) or end_row >= nrows(table):
            raise PDFReaderException(f'Fout in parse_table ({start_row}, {end_row}): de tabel heeft {nrows(table)} rijen.')
        if ncols(table) < 2:
            raise PDFReaderException(f'Fout in parse_table: de tabel heeft {ncols(table)} kolommen. Minimaal 2 kolommen worden verwacht.')
        for row in range(start_row, end_row):
            table_dict[table.values[row][0]] = table.values[row][1]
        self.__convert_fields(table_dict, translation_table, aanvraag_data)
    def __rectify_table(self, table, row0, row1):
        #necessary because some students somehow introduce \r characters in the table first column
        for row in range(row0, row1):
            if row1 < nrows(table):
                if isinstance(table.values[row][0], str): #sometimes there is an empty cell that is parsed by tabula as a float NAN
                    table.values[row][0] = table.values[row][0].replace('\r', '')
    def _parse_main_data(self, table: pd.DataFrame, aanvraag_data: _AanvraagData):        
        student_dict_fields = {'Student': 'student', 'Studentnummer': 'studnr', 'Telefoonnummer': 'telno', 'E-mailadres': 'email', 'Bedrijfsnaam': 'bedrijf'}
        student_dict_len  = len(student_dict_fields) + 5 # een beetje langer ivm bedrijfsnaam        
        self.__rectify_table(table, 0, student_dict_len)
        self.__merge_table_columns(table, 1, 2) # also an extreme case (Keanu Attema)
        self.__parse_table(table, 0, student_dict_len, student_dict_fields, aanvraag_data)
        self.parse_datum_str(table, aanvraag_data)        
    def parse_datum_str(self, table, aanvraag_data: _AanvraagData):
        # supports older version of form as well
        L = self.__get_strings_from_table(table, None, 'Student', 1)        
        aanvraag_data.datum_str = '/'.join(filter(lambda l: l != '', L))               
    def __merge_table_columns(self, table: pd.DataFrame, col1, col2):
        #normally this shouldnt be necessary, this covers an extreme case that was detected
        # [file: afstudeeropdracht SOgeti v9.pdf] where somehow tabula detected more than 1 column and inserted some NaNs.
        #this seems to correct that
        if ncols(table) > col2:            
            for row in range(0,nrows(table)):
                s = str(table.values[row][col1])                
                for col in range(col2,ncols(table)):
                     s += str(table.values[row][col])
                table.values[row][col1] = s
    def __parse_title(self, table:pd.DataFrame, aanvraag_data: _AanvraagData)->str:
        #regex because some students somehow lose the '.' characters or renumber the paragraphs, also older versions of the form have different paragraphs
        regex_versies = [{'start':'\d.*\(Voorlopige, maar beschrijvende\) Titel van de afstudeeropdracht', 'end':'\d.*Wat is de aanleiding voor de opdracht\?'},
                         {'start':'\d.*Titel van de afstudeeropdracht', 'end': '\d.*Korte omschrijving van de opdracht.*'},                        
                        ]
        self.__merge_table_columns(table, 0, 1)
        for versie in regex_versies:
            aanvraag_data.titel = ' '.join(self.__get_strings_from_table(table, versie['start'], versie['end'], 0))
            if aanvraag_data.titel:
                break

    def _parse_title(self, tables: list[pd.DataFrame], aanvraag_data: _AanvraagData)->str:
        for t in tables:
            if result := self.__parse_title(t, aanvraag_data):
                break
        return result
    def __get_strings_from_table(self, table:pd.DataFrame, start_paragraph_regex:str, end_paragraph_regex:str, column: int)->list[str]:
        def row_matches(table, row, pattern:re.Pattern):
            if isinstance(table.values[row][0], str):
                return pattern.match(table.values[row][0]) is not None
            else:
                return False
        def find_pattern(regex, row0):
            if not regex:
                return row0
            else:
                row = row0
                pattern = re.compile(regex)
                while row < nrows(table) and not row_matches(table, row, pattern):
                    row+=1
                return min(row + 1, nrows(table))
        row1 = find_pattern(start_paragraph_regex, 0)
        row2 = find_pattern(end_paragraph_regex, row1)
        result = []
        for row in range(row1, row2-1):
            result.append(table.values[row][column])
        return result
class AanvraagDataImporter(AanvraagProcessor):
    def __ask_titel(self, aanvraag: AanvraagInfo)->str:
        return tkinter.simpledialog.askstring(f'Titel', f'Titel voor {str(aanvraag)}') 
    def process(self, filename: str)->AanvraagInfo:
        logPrint(f'Lezen {filename}')
        if (aanvraag := AanvraagReaderFromPDF(filename).aanvraag):
            fileinfo = FileInfo(filename, timestamp=AUTOTIMESTAMP, filetype=FileType.AANVRAAG_PDF)
            if self.is_duplicate(fileinfo):            
                logWarn(f'Duplikaat: {filename}.\nal in database: {str(aanvraag)}')
                return None
            if not is_valid_email(aanvraag.student.email):
                new_email = try_extract_email(aanvraag.student.email, True)
                if new_email:
                    logWarn(f'Aanvraag email is ongeldig ({aanvraag.student.email}), aangepast als {new_email}.')
                    aanvraag.student.email = new_email
                else:
                    logError(f'Aanvraag email is ongeldig: {aanvraag.student.email}')
                    return None
            if not aanvraag.valid():
                logError(f'Aanvraag is ongeldig: {aanvraag}')
                return None    
            if not aanvraag.titel:
                aanvraag.titel=self.__ask_titel(aanvraag)
            logInfo(f'--- Start storing imported data from PDF {filename}')
            self.storage.create_aanvraag(aanvraag, fileinfo) 
            self.aanvragen.append(aanvraag)
            self.storage.commit()
            logInfo(f'--- Succes storing imported data from PDF {filename}')
            logPrint(aanvraag)
            return aanvraag
        return None
    def store_invalid(self, filename):
        self.storage.create_fileinfo(FileInfo(filename, AUTOTIMESTAMP, FileType.INVALID_PDF))
        self.storage.commit()
    def is_duplicate(self, file: FileInfo):
        return (stored:=self.storage.read_fileinfo(file.filename)) is not None and stored.timestamp == file.timestamp
        
def _import_aanvraag(filename: str, importer: AanvraagDataImporter):
    def is_already_processed(filename):
        if (fileinfo := importer.known_file_info(filename)):
            if fileinfo.filetype in [FileType.AANVRAAG_PDF,FileType.INVALID_PDF]: return  FileInfo.get_timestamp(filename) == fileinfo.timestamp
        else:
            return False
    try:
        if not is_already_processed(filename):    
            importer.process(filename)
    except PDFReaderException as E:
        logError(f'Fout bij importeren {filename}: {E}\n{ERRCOMMENT}')        
        importer.store_invalid(filename)

def import_directory(directory: str, storage: AAPStorage, recursive = True)->tuple[int,int]:
    def _get_pattern(recursive: bool):
        return '**/*.pdf' if recursive else '*.pdf' 
    min_id = storage.max_aanvraag_id() + 1
    if not Path(directory).is_dir():
        logWarn(f'Map {directory} bestaat niet. Afbreken.')
        return (min_id,min_id)
    logPrint(f'Start import van map  {directory}...')
    storage.add_file_root(str(directory))
    importer = AanvraagDataImporter(storage)
    for file in Path(directory).glob(_get_pattern(recursive)):
        _import_aanvraag(file, importer)
    max_id = storage.max_aanvraag_id()    
    logPrint(f'...Import afgerond')
    return (min_id, max_id)
        