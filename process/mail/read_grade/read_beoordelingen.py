from contextlib import contextmanager
from data.classes import AanvraagInfo, FileInfo, FileType
from general.log import log_print
from process.mail.read_grade.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen
from data.storage import AAPStorage

class WordDocumentGradeReader(GradeInputReader):
    @contextmanager
    def load_aanvraag(self, aanvraag: AanvraagInfo, doc_path: str):
        with self.open_document(doc_path=doc_path):
            yield self
    def read_data(self)->str:
        ROW_GRADE   = 6
        COL_VALUES  = 2
        if (table := self.find_table(1)):
            return self.read_table_cell(table, ROW_GRADE,COL_VALUES)
        else:
            return '--- tabel niet gevonden ---'
    def grade(self, aanvraag: AanvraagInfo)->str:
        return self.read_data()

class BeoordelingenFromWordDocument(BeoordelingenProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(WordDocumentGradeReader(), storage, aanvragen)
    def file_is_modified(self, aanvraag: AanvraagInfo, docpath):        
        registered_timestamp = aanvraag.files.get_timestamp(FileType.TO_BE_GRADED_DOCX)
        current_timestamp = FileInfo.get_timestamp(docpath)
        registered_digest  = aanvraag.files.get_digest(FileType.TO_BE_GRADED_DOCX)
        current_digest = FileInfo.get_digest(docpath) 
        return current_timestamp != registered_timestamp or current_digest != registered_digest
        #TODO: Er lijkt wat mis te gaan bij het opslaan van de digest, maar misschien valt dat mee. Gevolgen lijken mee te vallen.
    def must_process(self, aanvraag, docpath): 
        return self.file_is_modified(aanvraag, docpath)
    def get_empty_grade_error_message(self, grade, docpath, comment): 
        return f'kan beoordeling niet lezen: "{grade}" {docpath}...{comment}'

def read_beoordelingen_from_files(storage: AAPStorage, filter_func = None, preview=False):
    log_print('--- Verwerken beoordeelde formulieren...')
    verwerk_beoordelingen(BeoordelingenFromWordDocument(storage), storage=storage, filter_func = filter_func, preview=preview)
    log_print('--- Einde verwerken beoordeelde formulieren.')
