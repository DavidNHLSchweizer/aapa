from contextlib import contextmanager
from pathlib import Path
from data.classes import AUTOTIMESTAMP, AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.preview import pva
from general.singular_or_plural import sop
from process.general.old_aanvraag_processor import OldAanvraagProcessor
from general.fileutil import path_with_suffix
from process.general.word_processor import DocxWordDocument
from data.storage import AAPStorage
from general.log import log_error, log_info, log_print, log_warning

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

class BeoordelingenProcessor(OldAanvraagProcessor):
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
        aanvraag_path = aanvraag.aanvraag_source_file_name().parent
        graded_name = Path(aanvraag.files.get_filename(FileType.GRADED_DOCX)).name
        pdf_file_name = str(path_with_suffix(aanvraag_path.joinpath(graded_name), '.pdf').resolve())
        if not preview:
            pdf_file_name = self.reader.save_as_pdf(pdf_file_name)
        aanvraag.files.set_info(FileInfo(pdf_file_name, filetype=FileType.GRADED_PDF, aanvraag_id=aanvraag.id))
        log_print(f'\tFeedback file {pva(preview, "aan te maken", "aangemaakt")}: {pdf_file_name}.')
    def __adapt_files(self, aanvraag: AanvraagInfo, docpath: str, preview = False):
        self.__reset_to_be_graded_file(aanvraag)
        self.__store_graded_file(aanvraag, docpath)
        self.__create_graded_file_pdf(aanvraag, preview=preview)
    def __check_invalid_pdf(self, aanvraag: AanvraagInfo):
        #an earlier file with the same name as the GRADED_PDF may be registered als INVALID_PDF. remove this from storage and aanvraag.
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        if (f := self.known_file_info(filename)):
            log_info(f'removing previous registration for {filename}')
            aanvraag.files.reset_info(FileType.INVALID_PDF)
    def __storage_changes(self, aanvraag: AanvraagInfo):
        log_info(f'--- Start storing data for reading grade {aanvraag}')
        self.__check_invalid_pdf(aanvraag)        
        self.storage.aanvragen.update(aanvraag)
        self.storage.commit()
        log_info(f'--- End storing data for reading grade {aanvraag}')
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
        if not Path(docpath).is_file():
            log_error(f'Bestand {docpath} niet gevonden.')
            return False
        with self.reader.load_aanvraag(aanvraag, docpath) as document:
            if not (grade := self.reader.grade(aanvraag)):
                message = self.get_empty_grade_error_message(grade, docpath, aanvraagcomment)
                if message:
                    log_warning(message)
            elif (beoordeling := self.__check_grade(grade)) in [AanvraagBeoordeling.VOLDOENDE,AanvraagBeoordeling.ONVOLDOENDE]:
                log_print(f'Verwerken {aanvraag}: {beoordeling}')
                if document.modified:
                    document.save()
                result = self.__process_grade(aanvraag, docpath, beoordeling, preview=preview)        
            else:
                log_warning(f'{docpath}\n\tonverwachte beoordeling: "{grade}"\n\t{aanvraagcomment}')
        return result
    def must_process(self, aanvraag, docpath): 
        #to be implemented by subclass
        return False
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        if aanvraag.status != AanvraagStatus.NEEDS_GRADING:
            return False
        docpath = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
        if self.must_process(aanvraag, docpath):
            if self.process_file(aanvraag, docpath, preview=preview):
                return True
        return False  
    def process_all(self, filter_func = None, preview=False)->int:
        n_processed = 0
        for aanvraag in self.filtered_aanvragen(filter_func):
            if self.process(aanvraag, preview):
                n_processed  += 1
        return n_processed



def verwerk_beoordelingen(BP: BeoordelingenProcessor, storage: AAPStorage, filter_func = None, preview=False):
    log_info('--- Verwerken beoordelingen...', to_console=True)
    # BP=BeoordelingenFromWordDocument(storage)
    n_graded = BP.process_all(filter_func, preview=preview)
    log_info(f'### {n_graded} beooordeelde {sop(n_graded, "aanvraag", "aanvragen")}) {pva(preview, "te verwerken", "verwerkt")}', to_console=True)
    log_info('--- Einde verwerken beoordelingen.', to_console=True)
