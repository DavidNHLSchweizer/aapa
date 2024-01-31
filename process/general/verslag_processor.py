from typing import Iterable, Tuple
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.files import FileStorageAnalyzer, FilesQueries
from general.fileutil import file_exists, summary_string
from general.log import log_debug, log_error, log_print, log_warning
from process.general.base_processor import FileProcessor
from process.input.importing.aanvraag_importer import ImportException


class VerslagImporter(FileProcessor):
    def __init__(self, description: str, multiple = False):
        super().__init__(description)
        self.multiple = multiple
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:        
        queries: FilesQueries = storage.queries('files')
        status,stored_file = queries.analyze(filename)
        log_debug(f'MUST_PROCESS_FILE {filename}\n\treason: {status}  {stored_file}')
        match status:
            case FileStorageAnalyzer.Status.STORED | FileStorageAnalyzer.Status.STORED_INVALID:
                return False
            case _: return True
    def read_verslag(self)->Verslag:
        return None # implement in subclass
    def before_reading(self, preview = False):
        pass
    def after_reading(self, preview = False):
        pass
    def read_verslagen(self, filename: str, preview: bool)->Iterable[Tuple[Verslag, str]]:
        yield (None, '') # implement in subclass
    def process_file(self, filename: str, storage: AAPAStorage = None, preview=False)->Verslag|list[Verslag]:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {summary_string(filename, maxlen=100)}')
        result = None
        try:      
            self.before_reading(preview)
            if self.multiple:
                result = []
                for verslag in self.read_verslagen(filename, preview):
                    result.append(verslag)
                    # if validated := self._validate(storage, verslag_filename, verslag):
                    #     result.append(validated)
        except ImportException as exception:
            log_warning(f'{exception}.')           
        self.after_reading(preview)
        return result
