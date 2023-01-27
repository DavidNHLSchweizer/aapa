from contextlib import contextmanager
from pathlib import Path
import re
from data.aanvraag_info import AUTOTIMESTAMP, AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from data.aanvraag_processor import AanvraagProcessor
from general.fileutil import path_with_suffix
from office.word_processor import DocxWordDocument
from data.storage import AAPStorage
from general.log import logError, logInfo, logPrint

class BeoordelingError(Exception):pass

VOLDOENDE = 'voldoende'
def is_voldoende(beoordeling: str)->bool:
    return beoordeling.lower() == VOLDOENDE

class GradeInputReader(DocxWordDocument):    
    @contextmanager
    def load_aanvraag(self, aanvraag: AanvraagInfo, doc_path: str):
        pass       
    def grade(self, aanvraag: AanvraagInfo)->str:
        pass
    def flush(self):
        pass

class BeoordelingenProcessor(AanvraagProcessor):
    def __init__(self, reader: GradeInputReader, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None, graded_status = AanvraagStatus.GRADED):
        super().__init__(storage, aanvragen)
        self.reader = reader
        self.graded_status = graded_status
    def __reset_to_be_graded_file(self, aanvraag: AanvraagInfo):
        aanvraag.files.reset_info(FileType.TO_BE_GRADED_DOCX)
    def __store_graded_file(self, aanvraag: AanvraagInfo, docpath: str):
        self.reader.flush()
        aanvraag.files.set_info(FileInfo(docpath, timestamp=AUTOTIMESTAMP, filetype=FileType.GRADED_DOCX, aanvraag_id=aanvraag.id))
    def __create_graded_file_pdf(self, aanvraag: AanvraagInfo, preview=False):
        aanvraag_path = Path(aanvraag.files.get_filename(FileType.AANVRAAG_PDF)).parent
        graded_name = Path(aanvraag.files.get_filename(FileType.GRADED_DOCX)).name
        pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_name), '.pdf').resolve())
        if not preview:
            pdf_file_name = self.reader.save_as_pdf(pdf_file_name)
        aanvraag.files.set_info(FileInfo(pdf_file_name, filetype=FileType.GRADED_PDF, aanvraag_id=aanvraag.id))
        aangemaakt = 'aan te maken' if preview else 'aangemaakt'
        logPrint(f'Feedback file {aangemaakt}: {pdf_file_name}.')
    def __adapt_files(self, aanvraag: AanvraagInfo, docpath: str, preview = False):
        self.__reset_to_be_graded_file(aanvraag)
        self.__store_graded_file(aanvraag, docpath)
        self.__create_graded_file_pdf(aanvraag, preview=preview)
    def __check_invalid_pdf(self, aanvraag: AanvraagInfo):
        #an earlier file with the same name as the GRADED_PDF may be registered als INVALID_PDF. remove this from storage and aanvraag.
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        if (f := self.known_file_info(filename)):
            logInfo(f'removing previous registration for {filename}')
            aanvraag.files.reset_info(FileType.INVALID_PDF)
            self.storage.delete_fileinfo(filename)
    def __storage_changes(self, aanvraag: AanvraagInfo):
        logInfo(f'--- Start storing data for reading grade {aanvraag}')
        self.storage.update_aanvraag(aanvraag)
        self.storage.update_fileinfo(aanvraag.files.get_info(FileType.TO_BE_GRADED_DOCX))
        self.storage.update_fileinfo(aanvraag.files.get_info(FileType.GRADED_DOCX)) #note: the to_be_graded and graded hebben dezelfde naam
        self.__check_invalid_pdf(aanvraag)        
        self.storage.create_fileinfo(aanvraag.files.get_info(FileType.GRADED_PDF))
        self.storage.commit()
        logInfo(f'--- End storing data for reading grade {aanvraag}')
    def __adapt_aanvraag(self, aanvraag: AanvraagInfo, beoordeling: AanvraagBeoordeling)->bool:
        aanvraag.beoordeling = beoordeling
        aanvraag.status = self.graded_status
        return True
    def __process_grade(self, aanvraag: AanvraagInfo, docpath: str, beoordeling: AanvraagBeoordeling, preview=False)->bool:
        result = False
        if self.__adapt_aanvraag(aanvraag, beoordeling):
            result = True
        self.__adapt_files(aanvraag, docpath, preview=preview)
        self.__storage_changes(aanvraag)
        return result
    def __check_grade(self, grade: str)->AanvraagBeoordeling:
        match grade.split()[0].split(',')[0].lower():
            case 'voldoende':   return AanvraagBeoordeling.VOLDOENDE
            case 'onvoldoende': return AanvraagBeoordeling.ONVOLDOENDE
            case _: 
                return AanvraagBeoordeling.TE_BEOORDELEN
    def get_empty_grade_error_message(self, grade, docpath, comment): 
        return ''
    def process_file(self, aanvraag: AanvraagInfo, docpath: str, preview=False)->bool:
        result = False
        aanvraagcomment = f'Kan {aanvraag} niet verwerken.'
        with self.reader.load_aanvraag(aanvraag, docpath) as document:
            if not (grade := self.reader.grade(aanvraag)):
                message = self.get_empty_grade_error_message(grade, docpath, aanvraagcomment)
                if message:
                    logPrint(message)
            elif (beoordeling := self.__check_grade(grade)) in [AanvraagBeoordeling.VOLDOENDE,AanvraagBeoordeling.ONVOLDOENDE]:
                logPrint(f'Verwerken {aanvraag}: {beoordeling}')
                if document.modified:
                    document.save()
                result = self.__process_grade(aanvraag, docpath, beoordeling, preview=preview)        
            else:
                logPrint(f'{docpath}\n\tonverwachte beoordeling: "{grade}"\n\t{aanvraagcomment}')
        return result
    def must_process(self, aanvraag, docpath): 
        #to be implemented by subclass
        return False
    def process(self, filter_func = None, preview=False)->int:
        n_graded = 0
        for aanvraag in self.filtered_aanvragen(filter_func):
            if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
                continue            
            docpath = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
            if self.must_process(aanvraag, docpath):
                if self.process_file(aanvraag, docpath, preview=preview):
                    n_graded  += 1
        return n_graded

def verwerk_beoordelingen(BP: BeoordelingenProcessor, storage: AAPStorage, filter_func = None, preview=False):
    logPrint('--- Verwerken beoordelingen...')
    # BP=BeoordelingenFromWordDocument(storage)
    n_graded = BP.process(filter_func, preview=preview)
    verwerkt = 'te verwerken' if preview else 'verwerkt'
    logPrint(f'### {n_graded} beooordeelde aanvragen {verwerkt}')
    logPrint('--- Einde verwerken beoordelingen.')
