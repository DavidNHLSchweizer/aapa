from pathlib import Path
from copy import deepcopy
import re
import tkinter.simpledialog as tksimp
from data.classes.undo_logs import UndoLog
from data.storage.aapa_storage import AAPAStorage
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage.general.storage_const import StorageException
from data.storage.queries.aanvragen import AanvraagQueries
from data.storage.queries.files import FileStorageAnalyzer, FilesQueries
from debug.debug import MAJOR_DEBUG_DIVIDER
from general.log import log_debug, log_error, log_print, log_warning, log_info
from general.preview import pva
from general.singular_or_plural import sop
from general.timeutil import TSC
from general.valid_email import is_valid_email, try_extract_email
from general.config import ListValueConvertor, config
from general.fileutil import file_exists, summary_string
from process.general.aanvraag_pipeline import AanvraagCreatorPipeline
from process.general.aanvraag_processor import AanvraagCreator
from process.general.base_processor import FileProcessor
from process.general.pdf_aanvraag_reader import AanvraagReaderFromPDF, PDFReaderException, is_valid_title

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
        self.__insert_versie_en_kans()
        return True
    def __check_email(self)->bool:
        if not is_valid_email(self.validated_aanvraag.student.email):
            new_email = try_extract_email(self.validated_aanvraag.student.email, True)
            if new_email:
                new_email = new_email.lower()
                log_warning(f'Aanvraag email is ongeldig:\n\t({self.validated_aanvraag.student.email}),\n\taangepast als {new_email}.')
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
    def __insert_versie_en_kans(self):
        queries: AanvraagQueries = self.storage.queries('aanvragen')
        bedrijf = self.validated_aanvraag.bedrijf
        student = self.validated_aanvraag.student
        kans = queries.find_kans(student)
        self.validated_aanvraag.kans = (kans + 1) if kans else 1
        versie = queries.find_versie(student, bedrijf)
        self.validated_aanvraag.versie = (versie + 1) if versie else 1 
class AanvraagPDFImporter(FileProcessor):
    def __init__(self):
        super().__init__(description='PDF Importer')
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:        
        queries: FilesQueries = storage.queries('files')
        status,stored_file = queries.analyze(filename)
        log_debug(f'MUST_PROCESS_FILE {filename}\n\treason: {status}  {stored_file}')
        match status:
            case FileStorageAnalyzer.Status.STORED | FileStorageAnalyzer.Status.STORED_INVALID:
                return False
            case _: return True
    def process_file(self, filename: str, storage: AAPAStorage = None, preview=False)->Aanvraag:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {summary_string(filename, maxlen=100)}')
        try:      
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
    sop_aanvragen = sop(len(new_aanvragen), "aanvraag", "aanvragen", False)    
    if len(new_aanvragen):
        log_info(f'\t--- Nieuwe {sop_aanvragen} --- :')
        for aanvraag in new_aanvragen:
            log_print(f'\t{str(aanvraag)}')
    log_info(f'\t{len(new_aanvragen)} nieuwe {sop_aanvragen} {pva(preview, "te lezen", "gelezen")}.', to_console=True)

class DirectoryImporter(AanvraagCreatorPipeline): 
    def __init__(self, description: str, processor: AanvraagCreator, storage: AAPAStorage,                  
                 skip_directories: set[Path]={}, skip_files: list[str]=[]):
        super().__init__(description, processor, storage, activity=UndoLog.Action.SCAN, invalid_filetype=File.Type.INVALID_PDF)
        self.skip_directories:list[Path] = skip_directories
        self.skip_files:list[re.Pattern] = [re.compile(rf'{pattern}\.pdf', re.IGNORECASE) for pattern in skip_files]        
    def _in_skip_directory(self, filename: Path)->bool:
        for skip in self.skip_directories:
            if filename.is_relative_to(skip):
                return True
        return False
    def _skip_file(self, filename: Path)->bool:
        for pattern in self.skip_files:
            if pattern.match(str(filename)):
                return True 
        return False
    def _check_skip_file(self, filename: Path)->bool:
        skip_msg = ''
        warning = False
        queries: FilesQueries = self.storage.queries('files')
        status,stored_file = queries.analyze(filename)
        match status:
            case FileStorageAnalyzer.Status.STORED_INVALID_COPY:
                skip_msg = f'Overslaan: bestand {summary_string(filename, maxlen=100, initial=16)}\n\t is kopie van {summary_string(stored_file.filename, maxlen=100, initial=16)}'
                warning = True
            case FileStorageAnalyzer.Status.STORED_INVALID: 
                pass
            case FileStorageAnalyzer.Status.DUPLICATE:
                skip_msg = f'Bestand {summary_string(filename, maxlen=100, initial=16)} is kopie van\n\tbestand in database: {summary_string(stored_file.filename, maxlen=100, initial=16)}'          
                warning = True
            case _: 
                if self._skip_file(filename):
                    skip_msg = f'Overslaan: {summary_string(filename, maxlen=100)}'               
        if skip_msg:
            if warning:
                log_warning(skip_msg, to_console=True)
            else:
                log_print(skip_msg)
            self._add_invalid_file(str(filename))
            return True
        return False
    def _skip(self, filename: str)->bool:
        return self._in_skip_directory(filename) or self._check_skip_file(filename)

def import_directory(directory: str, output_directory: str, storage: AAPAStorage, recursive = True, preview=False)->int:
    def _get_pattern(recursive: bool):
        return '**/*.pdf' if recursive else '*.pdf'
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start import van map {directory}...', to_console=True)
    if Path(output_directory).is_relative_to(directory):
        log_warning(f'Directory {summary_string(output_directory)}\n\tis onderdeel van {summary_string(directory)}.\n\tWordt overgeslagen.', to_console=True)           
        skip_directories = {Path(output_directory)}
    else:
        skip_directories = set()
    skip_files = config.get('import', 'skip_files')
    importer = DirectoryImporter(f'Importeren aanvragen uit directory {directory}', AanvraagPDFImporter(), storage, skip_directories=skip_directories, skip_files=skip_files)
    first_id = storage.find_max_id('aanvragen') + 1
    log_debug(f'first_id: {first_id}')
    (n_processed, n_files) = importer.process(Path(directory).glob(_get_pattern(recursive)), preview=preview)    
    all_aanvragen = importer.storage.find_all('aanvragen', where_attributes='status', where_values=Aanvraag.Status.valid_states())
    report_imports(list(filter(lambda a: a.id >= first_id, all_aanvragen)), preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(n_processed, "nieuwe aanvraag", "nieuwe aanvragen")}. In directory: {sop(n_files, "bestand", "bestanden")})', to_console=True)
    log_debug(MAJOR_DEBUG_DIVIDER)
    return n_processed, n_files      