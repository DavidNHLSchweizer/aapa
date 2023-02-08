from contextlib import contextmanager
from data.classes import AanvraagInfo, FileInfo, FileType
from general.log import logPrint
from process.read_grade.verwerk_beoordeling import BeoordelingenProcessor, GradeInputReader, verwerk_beoordelingen
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
        registered_digest  = aanvraag.files.get_digest(FileType.TO_BE_GRADED_DOCX)
        current_version = FileInfo(docpath, filetype=FileType.TO_BE_GRADED_DOCX)
        return current_version.digest != registered_digest
        # return current_version.timestamp != registered_version or current_version.digest != registered_digest
    def must_process(self, aanvraag, docpath): 
        return self.file_is_modified(aanvraag, docpath)
    def get_empty_grade_error_message(self, grade, docpath, comment): 
        return f'kan beoordeling niet lezen: "{grade}" {docpath}...{comment}'

def read_beoordelingen_from_files(storage: AAPStorage, filter_func = None, preview=False):
    logPrint('--- Verwerken beoordeelde formulieren...')
    verwerk_beoordelingen(BeoordelingenFromWordDocument(storage), storage=storage, filter_func = filter_func, preview=preview)
    logPrint('--- Einde verwerken beoordeelde formulieren.')
