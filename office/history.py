from contextlib import contextmanager
import pandas as pd
from data.aanvraag_info import  AanvraagInfo, FileType, AanvraagStatus
from data.storage import AAPStorage
from general.log import logError, logPrint
from office.report_data import COLMAP
from office.import_data import nrows
from office.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen

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
    def __write_cell_value(table, rownr, colnr, value):
        try:
            table.Cell(Row=rownr,Column=colnr).Range.Text = value
        except Exception as E:
            print(E)
        return ''
    def __write_grade(self, grade):
    #write grade (from excel) to the file
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.find_table(WordDocumentGradeCreatorFromHistory.STUDENT_DATA_TABLE)):
            WordDocumentGradeCreatorFromHistory.__write_cell_value(table, ROW_GRADE,COL_VALUES, grade)
    def __write_history(self):        
        ROW_GENERAL   = 1
        COL_GENERAL   = 1
        if (table := self.find_table(WordDocumentGradeCreatorFromHistory.GENERAL_REMARKS_TABLE)):
            WordDocumentGradeCreatorFromHistory.__write_cell_value(table, ROW_GENERAL, COL_GENERAL, 'Beoordeling ingelezen uit Excel-bestand')
    def __create_grade_file(self, grade):
        self.__write_grade(grade)
        self.__write_history()
    @contextmanager
    def load_aanvraag(self, aanvraag: AanvraagInfo, doc_path: str):        
        self.aanvraag = aanvraag
        with self.open_document(doc_path=doc_path) as document:
            self.__create_grade_file(self.grade(aanvraag))
            yield document
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





# class HistoryProcessor(AanvraagProcessor):
#     def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
#         super().__init__(storage, aanvragen)
#         self.reader = None
#     # def file_is_modified(self, aanvraag: AanvraagInfo, docpath):
#     #     registered_version = aanvraag.files.get_timestamp(FileType.TO_BE_GRADED_DOCX)
#     #     current_version = FileInfo(docpath, filetype=FileType.TO_BE_GRADED_DOCX)
#     #     return current_version.timestamp != registered_version
#     def __reset_to_be_graded_file(self, aanvraag: AanvraagInfo):
#         aanvraag.files.reset_info(FileType.TO_BE_GRADED_DOCX)
#     # def __store_graded_file(self, aanvraag: AanvraagInfo, docpath: str):
#     #     aanvraag.files.set_info(FileInfo(docpath, timestamp=AUTOTIMESTAMP, filetype=FileType.GRADED_DOCX, aanvraag_id=aanvraag.id))
#     # def __create_graded_file_pdf(self, aanvraag: AanvraagInfo, preview=False):
#     #     aanvraag_path = Path(aanvraag.files.get_filename(FileType.AANVRAAG_PDF)).parent
#     #     graded_name = Path(aanvraag.files.get_filename(FileType.GRADED_DOCX)).name
#     #     pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_name), '.pdf').resolve())
#     #     if not preview:
#     #         pdf_file_name = self.reader.save_as_pdf(pdf_file_name)
#     #     aanvraag.files.set_info(FileInfo(pdf_file_name, filetype=FileType.GRADED_PDF, aanvraag_id=aanvraag.id))
#     #     aangemaakt = 'aan te maken' if preview else 'aangemaakt'
#     #     logPrint(f'Feedback file {aangemaakt}: {pdf_file_name}.')
#     def __adapt_aanvraag(self, aanvraag: AanvraagInfo, grade:str)->bool:
#         match(grade.lower()):
#             case 'voldoende':   aanvraag.beoordeling = AanvraagBeoordeling.VOLDOENDE
#             case 'onvoldoende': aanvraag.beoordeling = AanvraagBeoordeling.ONVOLDOENDE
#             case _: 
#                 aanvraag.beoordeling = AanvraagBeoordeling.TE_BEOORDELEN
#                 raise HistoryError(f'onverwachte beoordeling: "{grade}" ...\nKan {aanvraag} niet verwerken.')                
#         aanvraag.status = AanvraagStatus.GRADED
#         return True
#     def __adapt_files(self, aanvraag: AanvraagInfo, docpath: str, preview = False):
#         self.__reset_to_be_graded_file(aanvraag)
#         self.__store_graded_file(aanvraag, docpath)
#         self.__create_graded_file_pdf(aanvraag, preview=preview)
#     # def __check_invalid_pdf(self, aanvraag: AanvraagInfo):
#     #     #an earlier file with the same name as the GRADED_PDF may be registered als INVALID_PDF. remove this from storage and aanvraag.
#     #     filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
#     #     if (f := self.known_file_info(filename)):
#     #         logInfo(f'removing previous registration for {filename}')
#     #         aanvraag.files.reset_info(FileType.INVALID_PDF)
#     #         self.storage.delete_fileinfo(filename)
#     # def __storage_changes(self, aanvraag: AanvraagInfo):
#     #     logInfo(f'--- Start storing data for reading grade {aanvraag}')
#     #     self.storage.update_aanvraag(aanvraag)
#     #     self.storage.update_fileinfo(aanvraag.files.get_info(FileType.TO_BE_GRADED_DOCX))
#     #     self.storage.update_fileinfo(aanvraag.files.get_info(FileType.GRADED_DOCX)) #note: the to_be_graded and graded hebben dezelfde naam
#     #     self.__check_invalid_pdf(aanvraag)        
#     #     self.storage.create_fileinfo(aanvraag.files.get_info(FileType.GRADED_PDF))
#     #     self.storage.commit()
#     #     logInfo(f'--- End storing data for reading grade {aanvraag}')
#     def __create_beoordeling_pdf(self, aanvraag, grade, preview=False, )
#         doc_path = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
#         pdf_file_name = str(path_with_suffix(doc_path, '.pdf').resolve())
#         print(pdf_file_name)
#         self.BOM.process(doc_path, grade, pdf_file_name, preview=preview)

#     def __process_grade(self, aanvraag: AanvraagInfo, grade:str, preview=False)->bool:
#         result = False
#         if self.__adapt_aanvraag(aanvraag, grade):
#             result = True

#         self.__adapt_files(aanvraag, doc_path, preview=preview)
#         self.__storage_changes(aanvraag)
#         return result
#     def process_aanvraag(self, aanvraag: AanvraagInfo, preview=False)->bool:
#         result = False
#         try:
#             grade = self.reader.get_beoordeling(aanvraag)
#             logPrint(f'Verwerken {aanvraag}: {grade}')
#             result = self.__process_grade(aanvraag, grade, preview=preview)
#         except HistoryError as E:
#             logError(E)
#         return result
#     def process(self, xls_filename: str, filter_func = None, preview=False)->int:
#         self.reader = HistoryExcelReader(xls_filename)        
#         self.BOM = BeoordelingOordeelModifier()
#         n_graded = 0
#         for aanvraag in self.filtered_aanvragen(filter_func):
#             if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
#                 continue            
#             if self.process_aanvraag(aanvraag, preview=preview):
#                 n_graded  += 1
#         return n_graded
