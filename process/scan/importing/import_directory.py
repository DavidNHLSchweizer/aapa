from enum import Enum
from pathlib import Path
from copy import deepcopy
import tkinter.simpledialog as tksimp
from data.storage import AAPStorage
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.log import log_debug, log_error, log_print, log_warning, log_info
from general.preview import pva
from general.singular_or_plural import sop
from general.timeutil import TSC
from general.valid_email import is_valid_email, try_extract_email
from general.config import ListValueConvertor, config
from general.fileutil import file_exists, summary_string
from process.general.aanvraag_processor import AanvraagCreator, AanvragenCreator
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
    def __init__(self, storage: AAPStorage, source_file: str, aanvraag: Aanvraag):
        self.storage = storage
        self.source_file = source_file
        self.validated_aanvraag = deepcopy(aanvraag)
        self.student_changed = False
    def validate(self)->bool:
        if not self.__check_email():
            return False
        if not self.__check_titel():
            return False
        if not self.__check_sourcefile():
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
    def __check_sourcefile(self)->bool:
        file = File(self.source_file, timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, filetype=File.Type.AANVRAAG_PDF)
        if self.storage.files.is_duplicate(file):            
            log_warning(f'Duplikaat: {summary_string(self.source_file)}.\nal in database: {str(self.aanvraag)}')
            self.storage.files.store_invalid(self.source_file)
            return False
        self.validated_aanvraag.register_file(self.source_file, File.Type.AANVRAAG_PDF)
        return True

class AanvraagPDFImporter(AanvraagCreator):
    def must_process_file(self, filename: str, storage: AAPStorage, **kwargs)->bool:
        log_debug(f'must process file {filename}?')
        if self.is_known_invalid_file(filename, storage):
            return False
        if (stored := storage.files.find_digest(File.get_digest(filename))) and filename != stored.filename:
            log_warning(f'Bestand {summary_string(filename)} is kopie van\n\tbestand in database: {summary_string(stored.filename)}', to_console=True)
            storage.files.store_invalid(filename)
            return False
        return not stored or stored.filetype not in {File.Type.AANVRAAG_PDF, File.Type.COPIED_PDF}
    def process_file(self, filename: str, storage: AAPStorage = None, preview=False)->Aanvraag:
        if not file_exists(filename):
            log_error(f'Bestand {filename} niet gevonden.')
            return None
        log_print(f'Lezen {summary_string(filename, maxlen=100)}')
        try:
            if (aanvraag := AanvraagReaderFromPDF(filename).aanvraag):
                validator = AanvraagValidator(storage, filename, aanvraag)
                if not validator.validate():
                    return None
                else:
                    log_print(f'\t{str(validator.validated_aanvraag)}')
                    return validator.validated_aanvraag
            else:
                return None
        except PDFReaderException as reader_exception:
            storage.files.store_invalid(filename)
            log_warning(f'{reader_exception}\n\t{ERRCOMMENT}.')           
        return None


class ImportResult(Enum):
    UNKNOWN  = 0
    IMPORTED = 1
    ERROR    = 2
    ALREADY_IMPORTED = 3
    KNOWN_ERROR = 4
    KNOWN_PDF = 5
    COPIED_FILE = 6

# def _import_aanvraag(filename: str, importer: AanvraagDataImporter)->ImportResult:
#     def known_import_result(filename)->ImportResult:
#         def not_changed(filename, file):
#             return File.get_timestamp(filename) == file.timestamp and File.get_digest(filename) == file.digest
#         if (file := importer.known_file_info(filename)):
#             match file.filetype:
#                 case File.Type.AANVRAAG_PDF | File.Type.COPIED_PDF:
#                     if not_changed(filename, file): 
#                         return ImportResult.ALREADY_IMPORTED if file.filetype == File.Type.AANVRAAG_PDF else ImportResult.COPIED_FILE
#                     else:
#                         return ImportResult.UNKNOWN
#                 case File.Type.GRADED_PDF:
#                     return ImportResult.KNOWN_PDF
#                 case File.Type.INVALID_PDF:
#                     if not_changed(filename, file): 
#                         return ImportResult.KNOWN_ERROR
#                     else:
#                         return ImportResult.UNKNOWN
                
#         return ImportResult.UNKNOWN
#     try:
#         if (result := known_import_result(filename)) == ImportResult.UNKNOWN: 
#             if importer.process_file(filename): 
#                 return ImportResult.IMPORTED
#             else:
#                 return ImportResult.ERROR
#         return result
#     except ImportException as E:
#         log_error(f'Fout bij importeren {filename}:\n\t{E}\n\t{ERRCOMMENT}')        
#         importer.storage.file_info.store_invalid(filename)
#         return ImportResult.ERROR

def report_imports(file_results:dict, new_aanvragen, preview=False, verbose=False):
    def import_status_str(result):
        match result:
            case ImportResult.IMPORTED: return pva(preview, "te importeren","geimporteerd")
            case ImportResult.ERROR: return pva(preview, "kan niet worden geimporteerd","fout bij importeren")
            case ImportResult.ALREADY_IMPORTED: return "eerder geimporteerd"
            case ImportResult.COPIED_FILE: return "kopie van aanvraag (eerder geimporteerd)"
            case ImportResult.KNOWN_ERROR: return "eerder gelezen, kan niet worden geimporteerd"
            case _: return "???"
    def file_str(file,result):
        return f'{summary_string(file)} [{import_status_str(result)}]'
    log_info('Rapportage import:', to_console=True)
    sop_aanvragen = sop(len(new_aanvragen), "aanvraag", "aanvragen")    
    if verbose:
        log_info(f'\t---Gelezen {sop_aanvragen}:---')
        if len(new_aanvragen):
            log_print('\t\t'+ '\n\t\t'.join([file_str(file, result) for file,result in file_results.items()]))
    if len(new_aanvragen):
        log_info(f'\t--- Nieuwe {sop_aanvragen} --- :')
        log_print('\t\t'+'\n\t\t'.join([str(aanvraag) for aanvraag in new_aanvragen]))
    log_info(f'\t{len(new_aanvragen)} nieuwe {sop_aanvragen} {pva(preview, "te lezen", "gelezen")}.', to_console=True)

class DirectoryImporter(AanvragenCreator): pass

def import_directory(directory: str, output_directory: str, storage: AAPStorage, recursive = True, preview=False)->int:
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
    file_results = {}
    first_id = storage.aanvragen.max_id() + 1
    #TODO: hier zorgen voor resultaten bij het importeren, misschien, lijkt niet echt meerwaarde te hebben met de nieuwe procesgang
    n_processed = importer.process_files(Path(directory).glob(_get_pattern(recursive)), preview=preview)
    report_imports(file_results, importer.storage.aanvragen.read_all(lambda x: x.id >= first_id), preview=preview)
    log_info(f'...Import afgerond ({n_processed} {sop(n_processed, "bestand", "bestanden")})', to_console=True)
    return n_processed       