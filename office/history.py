from contextlib import contextmanager
import pandas as pd
from data.aanvraag_info import  AanvraagInfo, FileType, AanvraagStatus
from data.storage import AAPStorage
from general.log import logError, logPrint
from office.report_data import COLMAP
from office.import_data import nrows
from office.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen
from office.word_processor import DocxWordDocument

class HistoryError(Exception): pass

class HistoryExcelReader:
    NOTFOUND = -1
    def __init__(self, filename:str):
        self.filename = filename
        self.table = pd.read_excel(self.filename)
        self.table.fillna(value='',inplace=True) 
        self.__check_compatible_columns()            
    def __check_compatible_columns(self):
        for r, column in enumerate(self.table.columns):
            if COLMAP.get(column, -1) != r:
                raise HistoryError(f'Unexpected column "{column}" in {self.filename}')
    def _row_for_aanvraag(self, aanvraag: AanvraagInfo)->int:
        for row in range(nrows(self.table)):
            if self.__match_row(aanvraag, row):
                return row
        return HistoryExcelReader.NOTFOUND
    def get_beoordeling(self, aanvraag: AanvraagInfo):
        if (row:=self._row_for_aanvraag(aanvraag)) != HistoryExcelReader.NOTFOUND:
            return self.__table_row_get(row, 'beoordeling')
        return None        
    def __table_row_get(self, row, col_name):
        return self.table.values[row, COLMAP[col_name]]
    def __match_row(self, aanvraag: AanvraagInfo, row: int)->bool:
        if aanvraag.titel != self.__table_row_get(row, 'titel') or aanvraag.student.studnr != str(self.__table_row_get(row, 'studentnr')) or\
            aanvraag.bedrijf.bedrijfsnaam != self.__table_row_get(row, 'bedrijf'):
            return False
        if aanvraag.files.get_timestamp(FileType.AANVRAAG_PDF) != self.__table_row_get(row, 'timestamp'):
            return False
        return True

class WordDocumentGradeCreatorFromHistory(GradeInputReader):
    STUDENT_DATA_TABLE = 1
    GENERAL_REMARKS_TABLE = 2
    def __init__(self, xls_filename):
        super().__init__()
        self.info_from_excel = HistoryExcelReader(xls_filename)     
        self.aanvraag = None   
    def __write_grade(self, grade):
    #write grade (from excel) to the file
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.find_table(WordDocumentGradeCreatorFromHistory.STUDENT_DATA_TABLE)):
            self.write_table_cell(table, ROW_GRADE, COL_VALUES, grade)
    def __write_history(self):        
        ROW_GENERAL   = 1
        COL_GENERAL   = 1
        if (table := self.find_table(WordDocumentGradeCreatorFromHistory.GENERAL_REMARKS_TABLE)):
            self.write_table_cell(table, ROW_GENERAL, COL_GENERAL, 'Beoordeling ingelezen uit Excel-bestand')
    def __create_grade_file(self, grade):
        self.__write_grade(grade)
        self.__write_history()        
    @contextmanager    
    def load_aanvraag(self, aanvraag: AanvraagInfo, doc_path: str):        
        self.aanvraag = aanvraag
        with self.open_document(doc_path=doc_path):
            self.__create_grade_file(self.grade(aanvraag))            
            yield self
    def grade(self, aanvraag: AanvraagInfo)->str:
        return self.info_from_excel.get_beoordeling(aanvraag)


class BeoordelingenFromExcelfile(BeoordelingenProcessor):
    def __init__(self, xls_filename: str, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(WordDocumentGradeCreatorFromHistory(xls_filename), storage, aanvragen, graded_status=AanvraagStatus.READY_IMPORTED)
    def file_is_modified(self, aanvraag: AanvraagInfo, docpath):        
        return aanvraag.beoordeling != self.reader.grade(aanvraag)
    def must_process(self, aanvraag, docpath): 
        return self.file_is_modified(aanvraag, docpath)

def read_beoordelingen_from_files(xls_filename: str, storage: AAPStorage, filter_func = None, preview=False):
    logPrint(f'--- Verwerken beoordeelde aanvragen (uit {xls_filename})...')
    verwerk_beoordelingen(BeoordelingenFromExcelfile(xls_filename, storage), storage=storage, filter_func = filter_func, preview=preview)
    logPrint(f'--- Einde verwerken beoordeelde aanvragen (uit {xls_filename}).')


