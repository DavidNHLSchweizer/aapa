from pathlib import Path
from copy import deepcopy
import tkinter.simpledialog as tksimp
from data.storage import AAPAStorage
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.log import log_error, log_print, log_warning, log_info
from general.preview import pva
from general.singular_or_plural import sop
from general.timeutil import TSC
from general.valid_email import is_valid_email, try_extract_email
from general.config import ListValueConvertor, config
from general.fileutil import file_exists, summary_string
from process.general.aanvraag_processor import AanvraagCreator
from process.general.pdf_aanvraag_reader import AanvraagReaderFromPDF, PDFReaderException, is_valid_title
from process.general.pipeline import CreatingPipeline

def init_config():
    config.register('import', 'skip_files', ListValueConvertor)
    config.init('import', 'skip_files', ['.*Aanvraag toelating afstuderen.*', 
                '.*Beoordeling.*verslag.*', '.*Plan van aanpak.*', '.*Beoordeling aanvraag.*',
                '.*Onderzoeksverslag.*', '.*Technisch verslag.*'])
init_config()

ERRCOMMENT = 'Waarschijnlijk niet een aanvraagformulier'
class ImportException(Exception): pass
NOTFOUND = 'NOT FOUND'

class AanvraagValidator:
    def __init__(self, storage: AAPAStorage, source_file: str, aanvraag: Aanvraag):
        self.storage = storage
        self.source_file = source_file
        self.validated_aanvraag = deepcopy(aanvraag)
        self.student_changed = False
    def validate(self)->bool:
        if not self.__check_email():
            return False
        if not self.__check_titel():
            return False
        return True
    def __check_email(self)->bool:
        if not is_valid_email(self.validated_aanvraag.student.email):
            new_email = try_extract_email(self.validated_aanvraag.student.email, True)
            if new_email:
                log_warning(f'Aanvraag email is ongeldig ({self.validated_aanvraag.student.email}), aangepast als {new_email}.')
                self.validated_aanvraag.student.email = new_email
                self.student_changed = True
            else:
                log_error(f'Aanvraag email is ongeldig: {self.validated_aanvraag.student.email}')
                return False
        return True
    def __check_titel(self)->bool:
        if not is_valid_title(self.validated_aanvraag.titel):
            self.validated_aanvraag.titel=self.__ask_titel(self.validated_aanvraag)
        return True
    def __ask_titel(self, aanvraag: Aanvraag)->str:
        return tksimp.askstring(f'Titel', f'Titel voor {str(aanvraag)}', initialvalue=aanvraag.titel)

class AanvraagPDFImporter(AanvraagCreator):
    def __init__(self, entry_states: set[Aanvraag.Status] = None, exit_state: Aanvraag.Status = None):
        super().__init__(entry_states=entry_states, exit_state=exit_state, description='PDF Importer')
    def __check_duplicate(self, filename: str, storage: AAPAStorage)->bool:
        if storage.files.is_duplicate(filename, File.get_digest(filename)):            
            stored_filename = storage.files.find_digest(File.get_digest(filename)).filename
            log_warning(f'Bestand {summary_string(filename)} is kopie van\n\tbestand in database: {summary_string(stored_filename)}', to_console=True)
            return True
        return False
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:
        if self.is_known_invalid_file(filename, storage): 
            return False
        # if (stored := storage.files.find_digest(File.get_digest(filename))) and filename != stored.filename:
        #     log_warning(f'Bestand {summary_string(filename)} is kopie van\n\tbestand in database: {summary_string(stored.filename)}', to_console=True)
        #     return False
        return True #not stored or stored.filetype not in {File.Type.AANVRAAG_PDF, File.Type.COPIED_PDF}
    def process_file(self, filename: str, storage: AAPAStorage = None, preview=False)->Aanvraag:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {summary_string(filename, maxlen=100)}')
        try:      
            if self.__check_duplicate(filename, storage):
                return None
            if (aanvraag := AanvraagReaderFromPDF(filename).read_aanvraag()):
                validator = AanvraagValidator(storage, filename, aanvraag)
                if not validator.validate():
                    return None
                else:
                    log_print(f'\t{str(validator.validated_aanvraag)}')
                    validator.validated_aanvraag.register_file(filename, File.Type.AANVRAAG_PDF)
                    return validator.validated_aanvraag
            else:
                return None
        except PDFReaderException as reader_exception:
            log_warning(f'{reader_exception}\n\t{ERRCOMMENT}.')           
        return None

def report_imports(new_aanvragen, preview=False, verbose=False):
    log_info('Rapportage import:', to_console=True)
    if not new_aanvragen:
        new_aanvragen = []
    sop_aanvragen = sop(len(new_aanvragen), "aanvraag", "aanvragen")    
    if len(new_aanvragen):
        log_info(f'\t--- Nieuwe {sop_aanvragen} --- :')
        log_print('\t\t'+'\n\t\t'.join([str(aanvraag) for aanvraag in new_aanvragen]))
    log_info(f'\t{len(new_aanvragen)} nieuwe {sop_aanvragen} {pva(preview, "te lezen", "gelezen")}.', to_console=True)

class DirectoryImporter(CreatingPipeline): pass

def import_directory(directory: str, output_directory: str, storage: AAPAStorage, recursive = True, preview=False)->int:
    def _get_pattern(recursive: bool):
        return '**/*.pdf' if recursive else '*.pdf'
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start import van map  {directory}...', to_console=True)
    if Path(output_directory).is_relative_to(directory):
        log_warning(f'Directory {summary_string(output_directory)}\n\tis onderdeel van {summary_string(directory)}.\n\tWordt overgeslagen.', to_console=True)           
        skip_directories = {Path(output_directory)}
    else:
        skip_directories = set()
    skip_files = config.get('import', 'skip_files')
    importer = DirectoryImporter(f'Importeren aanvragen uit directory {directory}', AanvraagPDFImporter(), storage, skip_directories=skip_directories, skip_files=skip_files)
    first_id = storage.aanvragen.max_id() + 1
    n_processed = importer.process(Path(directory).glob(_get_pattern(recursive)), preview=preview)    
    report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    log_info(f'...Import afgerond ({n_processed} {sop(n_processed, "bestand", "bestanden")})', to_console=True)
    return n_processed       