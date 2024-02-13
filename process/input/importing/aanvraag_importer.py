from typing import Iterable, Tuple
from data.classes.aanvragen import Aanvraag
from data.general.const import MijlpaalType
from data.classes.files import File
from storage.aapa_storage import AAPAStorage
from storage.queries.files import FileStorageAnalyzer, FilesQueries
from general.fileutil import file_exists
from main.log import log_debug, log_error, log_print, log_warning
from process.general.base_processor import FileProcessor
from process.general.pdf_aanvraag_reader import PDFReaderException
from process.general.student_dir_builder import SDB
from process.input.importing.aanvraag_validator import AanvraagValidator

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class ImportException(Exception): pass
NOTFOUND = 'NOT FOUND'

class AanvraagImporter(FileProcessor):
    def __init__(self, description: str, multiple = False):
        super().__init__(description)
        self.multiple = multiple
    def _validate(self, storage: AAPAStorage, filename:str, aanvraag: Aanvraag)->Aanvraag:
        validator = AanvraagValidator(storage, filename, aanvraag)
        if not validator.validate():
            return None
        else:
            log_print(f'\t{str(validator.validated_aanvraag)}')
            return validator.validated_aanvraag
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:        
        queries: FilesQueries = storage.queries('files')
        status,stored_file = queries.analyze(filename)
        log_debug(f'MUST_PROCESS_FILE {filename}\n\treason: {status}  {stored_file}')
        match status:
            case FileStorageAnalyzer.Status.STORED | FileStorageAnalyzer.Status.STORED_INVALID:
                return False
            case _: return True
    def read_aanvraag(self, filename: str)->Aanvraag:
        return None # implement in subclass
    def _register_aanvraag(self, aanvraag: Aanvraag, filename: str, storage: AAPAStorage):
        aanvraag.register_file(filename, File.Type.AANVRAAG_PDF, MijlpaalType.AANVRAAG)
        SDB(storage).register_file(student=aanvraag.student, 
                                                            datum=File.get_timestamp(filename) if file_exists(filename) else aanvraag.datum,
                                                            filename=filename, 
                                                            filetype=File.Type.AANVRAAG_PDF,mijlpaal_type=MijlpaalType.AANVRAAG)
    def before_reading(self, preview = False):
        pass
    def after_reading(self, preview = False):
        pass
    def read_aanvragen(self, filename: str, preview: bool)->Iterable[Tuple[Aanvraag, str]]:
        yield (None, '') # implement in subclass
    def process_file(self, filename: str, storage: AAPAStorage = None, preview=False)->Aanvraag|list[Aanvraag]:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {File.display_file(filename)}')
        result = None
        try:      
            self.before_reading(preview)
            if self.multiple:
                result = []
                for (aanvraag,aanvraag_filename) in self.read_aanvragen(filename, preview):
                    if validated := self._validate(storage, aanvraag_filename, aanvraag):
                        result.append(validated)
                        self._register_aanvraag(validated, aanvraag_filename, storage)
            elif (aanvraag := self.read_aanvraag(filename)):
                result = self._validate(storage, filename, aanvraag)
                if result: 
                    self._register_aanvraag(result, filename, storage)
        except (ImportException,PDFReaderException) as exception:
            log_warning(f'{exception}\n\t{ERRCOMMENT}.')           
        self.after_reading(preview)
        return result
