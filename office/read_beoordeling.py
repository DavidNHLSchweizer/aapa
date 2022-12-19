
from pathlib import Path
from data.aanvraag_info import AUTOTIMESTAMP, AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from data.aanvraag_processor import AanvraagProcessor
from office.word_reader import WordReader, WordReaderException
from data.storage import AAPStorage
from general.log import logError, logInfo, logPrint, logWarn



VOLDOENDE = 'voldoende'
def is_voldoende(beoordeling: str)->bool:
    return beoordeling.lower() == VOLDOENDE

class BeoordelingOordeelReader(WordReader):
    #read grade from the file
    def read_data(self)->str:
        def read_cell_value(table, rownr, colnr)->str:
            try:
                cell_text = table.Cell(Row=rownr,Column=colnr).Range.Text
                # returned cell_text for some reason ends with both an 0x0d and a 0x07
                return cell_text[:-2]
            except Exception as E:
                print(E)
            return ''
        ROW_GRADE   = 5
        COL_VALUES  = 2
        if (table := self.__find_table()):
            return (read_cell_value(table, ROW_GRADE,COL_VALUES))
        else:
            return ''
    def __find_table(self):
        if self.document.Tables.Count > 0:
            return self.document.Tables(1)
        else:
            return None

class BeoordelingenReaderProcessor(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.reader = BeoordelingOordeelReader()
    def file_is_modified(self, aanvraag: AanvraagInfo, docpath):
        registered_version = aanvraag.files.get_timestamp(FileType.TO_BE_GRADED_DOCX)
        current_version = FileInfo(docpath, filetype=FileType.TO_BE_GRADED_DOCX)
        return current_version.timestamp != registered_version
    def __reset_to_be_graded_file(self, aanvraag: AanvraagInfo):
        aanvraag.files.reset_info(FileType.TO_BE_GRADED_DOCX)
    def __store_graded_file(self, aanvraag: AanvraagInfo, docpath: str):
        aanvraag.files.set_info(FileInfo(docpath, timestamp=AUTOTIMESTAMP, filetype=FileType.GRADED_DOCX, aanvraag_id=aanvraag.id))
    def __create_graded_file_pdf(self, aanvraag: AanvraagInfo):
        pdf_file_name = self.reader.save_as_pdf()
        aanvraag.files.set_info(FileInfo(pdf_file_name, filetype=FileType.GRADED_PDF, aanvraag_id=aanvraag.id))
        logPrint(f'Feedback file aangemaakt: {pdf_file_name}.')
    def __adapt_aanvraag(self, aanvraag: AanvraagInfo, docpath: str, grade:str)->bool:
        match(grade.lower()):
            case 'voldoende':   aanvraag.beoordeling = AanvraagBeoordeling.VOLDOENDE
            case 'onvoldoende': aanvraag.beoordeling = AanvraagBeoordeling.ONVOLDOENDE
            case _: 
                aanvraag.beoordeling = AanvraagBeoordeling.TE_BEOORDELEN
                raise WordReaderException(f'onverwachte beoordeling: "{grade}" in bestand {docpath}...\nKan {aanvraag} niet verwerken.')                
        aanvraag.status = AanvraagStatus.GRADED
        return True
    def __adapt_files(self, aanvraag: AanvraagInfo, docpath: str):
        self.__reset_to_be_graded_file(aanvraag)
        self.__store_graded_file(aanvraag, docpath)
        self.__create_graded_file_pdf(aanvraag)
    def __storage_changes(self, aanvraag: AanvraagInfo):
        logInfo(f'--- Start storing data for reading grade {aanvraag}')
        self.storage.update_aanvraag(aanvraag)
        self.storage.update_fileinfo(aanvraag.files.get_info(FileType.TO_BE_GRADED_DOCX))
        self.storage.update_fileinfo(aanvraag.files.get_info(FileType.GRADED_DOCX)) #note: the to_be_graded and graded hebben dezelfde naam
        self.storage.create_fileinfo(aanvraag.files.get_info(FileType.GRADED_PDF))
        self.storage.commit()
        logInfo(f'--- End storing data for reading grade {aanvraag}')
    def __process_grade(self, aanvraag: AanvraagInfo, docpath: str, grade:str)->bool:
        result = False
        if self.__adapt_aanvraag(aanvraag, docpath, grade):
            result = True
        self.__adapt_files(aanvraag, docpath)
        self.__storage_changes(aanvraag)
        return result
    def process_file(self, aanvraag: AanvraagInfo, docpath: str)->bool:
        result = False
        try:
            self.reader.open_document(docpath)
            grade = self.reader.read_data()
            logPrint(f'Verwerken {aanvraag}: {grade}')
            result = self.__process_grade(aanvraag, docpath, grade)
        except WordReaderException as E:
            logError(E)
        finally:
            self.reader.close()
        return result

    def process(self, filter_func = None)->int:
        n_graded = 0
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
                continue            
            docpath = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
            if self.file_is_modified(aanvraag, docpath):
                if self.process_file(aanvraag, docpath):
                    n_graded  += 1
        return n_graded

def read_beoordelingen_files(storage: AAPStorage, filter_func = None):
    logPrint('--- Verwerken beoordeelde formulieren...')
    BP=BeoordelingenReaderProcessor(storage)
    n_graded = BP.process(filter_func)
    logPrint(f'### {n_graded} beooordeelde aanvragen verwerkt')
    logPrint('--- Einde verwerken beoordeelde formulieren.')
