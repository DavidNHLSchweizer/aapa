from contextlib import contextmanager
import pandas as pd
from data.classes.aanvragen import  Aanvraag
from data.classes.files import File
from data.storage import AAPAStorage
from general.log import log_print
from data.report_data import COLMAP
#TODO: HISTORY bijwerken
# from process.mail.read_grade.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen

# def nrows(table: pd.DataFrame)->int:
#     return table.shape[0]
# def ncols(table: pd.DataFrame)->int:
#     return table.shape[1]

# class HistoryError(Exception): pass

# class HistoryExcelReader:
#     NOTFOUND = -1
#     def __init__(self, filename:str):
#         self.filename = filename
#         self.table = pd.read_excel(self.filename)
#         self.table.fillna(value='',inplace=True) 
#         self.__check_compatible_columns()            
#     def __check_compatible_columns(self):
#         for r, column in enumerate(self.table.columns):
#             if COLMAP.value(column) != r:
#                 raise HistoryError(f'Unexpected column "{column}" in {self.filename}')
#     def _row_for_aanvraag(self, aanvraag: Aanvraag)->int:
#         for row in range(nrows(self.table)):
#             if self.__match_row(aanvraag, row):
#                 return row
#         return HistoryExcelReader.NOTFOUND
#     def get_beoordeling(self, aanvraag: Aanvraag):
#         if (row:=self._row_for_aanvraag(aanvraag)) != HistoryExcelReader.NOTFOUND:
#             return self.__table_row_get(row, 'beoordeling')
#         return None        
#     def __table_row_get(self, row, col_name):
#         return self.table.values[row, COLMAP.value(col_name)]
#     def __match_row(self, aanvraag: Aanvraag, row: int)->bool:
#         if aanvraag.titel != self.__table_row_get(row, 'titel') or aanvraag.student.stud_nr != str(self.__table_row_get(row, 'studentnr')) or\
#             aanvraag.bedrijf.name != self.__table_row_get(row, 'bedrijf'):
#             return False
#         if aanvraag.files.get_timestamp(File.Type.AANVRAAG_PDF) != self.__table_row_get(row, 'timestamp'):
#             return False
#         return True

# class WordDocumentGradeCreatorFromHistory(GradeInputReader):
#     STUDENT_DATA_TABLE = 1
#     GENERAL_REMARKS_TABLE = 2
#     def __init__(self, xls_filename):
#         super().__init__()
#         self.info_from_excel = HistoryExcelReader(xls_filename)     
#         self.aanvraag = None   
#     def __write_grade(self, grade):
#     #write grade (from excel) to the file
#         ROW_GRADE   = 6
#         COL_VALUES  = 2
#         if (table := self.find_table(WordDocumentGradeCreatorFromHistory.STUDENT_DATA_TABLE)):
#             self.write_table_cell(table, ROW_GRADE, COL_VALUES, grade)
#     def __write_history(self):        
#         ROW_GENERAL   = 1
#         COL_GENERAL   = 1
#         if (table := self.find_table(WordDocumentGradeCreatorFromHistory.GENERAL_REMARKS_TABLE)):
#             self.write_table_cell(table, ROW_GENERAL, COL_GENERAL, 'Beoordeling ingelezen uit Excel-bestand')
#     def __create_grade_file(self, grade):
#         self.__write_grade(grade)
#         self.__write_history()        
#     @contextmanager    
#     def load_aanvraag(self, aanvraag: Aanvraag, doc_path: str):        
#         self.aanvraag = aanvraag
#         with self.open_document(doc_path=doc_path):
#             self.__create_grade_file(self.grade(aanvraag))            
#             yield self
#     def grade(self, aanvraag: Aanvraag)->str:
#         return self.info_from_excel.get_beoordeling(aanvraag)


# class BeoordelingenFromExcelfile(BeoordelingenProcessor):
#     def __init__(self, xls_filename: str, storage: AAPStorage, aanvragen: list[Aanvraag] = None):
#         super().__init__(WordDocumentGradeCreatorFromHistory(xls_filename), storage, aanvragen, graded_status=Aanvraag.Status.READY_IMPORTED)
#     def file_is_modified(self, aanvraag: Aanvraag, docpath):        
#         return aanvraag.beoordeling != self.reader.grade(aanvraag)
#     def must_process(self, aanvraag, docpath): 
#         return self.file_is_modified(aanvraag, docpath)

def read_beoordelingen_from_files(xls_filename: str, storage: AAPAStorage, filter_func = None, preview=False):
    log_print(f'--- Verwerken beoordeelde aanvragen (uit {xls_filename})...')
    # verwerk_beoordelingen(BeoordelingenFromExcelfile(xls_filename, storage), storage=storage, filter_func = filter_func, preview=preview)
    log_print(f'--- Einde verwerken beoordeelde aanvragen (uit {xls_filename}).')


