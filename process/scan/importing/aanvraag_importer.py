from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.files import FileStorageAnalyzer, FilesQueries
from general.fileutil import file_exists, summary_string
from general.log import log_debug, log_error, log_print, log_warning
from process.general.base_processor import FileProcessor
from process.general.student_dir_builder import StudentDirectoryBuilder
from process.scan.importing.aanvraag_validator import AanvraagValidator

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class ImportException(Exception): pass
NOTFOUND = 'NOT FOUND'

class AanvraagImporter(FileProcessor):
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
    
    def process_file(self, filename: str, storage: AAPAStorage = None, preview=False)->Aanvraag:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {summary_string(filename, maxlen=100)}')
        try:      
            if (aanvraag := self.read_aanvraag(filename)):
                validator = AanvraagValidator(storage, filename, aanvraag)
                if not validator.validate():
                    return None
                else:
                    log_print(f'\t{str(validator.validated_aanvraag)}')
                    validator.validated_aanvraag.register_file(filename, File.Type.AANVRAAG_PDF, MijlpaalType.AANVRAAG)
                    StudentDirectoryBuilder(storage).register_file(student=validator.validated_aanvraag.student, 
                                                                   datum=File.get_timestamp(filename),
                                                                   filename=filename, 
                                                                   filetype=File.Type.AANVRAAG_PDF,mijlpaal_type=MijlpaalType.AANVRAAG)
                    return validator.validated_aanvraag
            else:
                return None
        except ImportException as exception:
            log_warning(f'{exception}\n\t{ERRCOMMENT}.')           
        return None
