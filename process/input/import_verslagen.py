from pathlib import Path
from data.classes.undo_logs import UndoLog
from data.classes.verslagen import Verslag
from storage.aapa_storage import AAPAStorage
from storage.queries.verslagen import VerslagQueries
from debug.debug import MAJOR_DEBUG_DIVIDER
from main.log import log_debug, log_error, log_print, log_info
from process.general.preview import pva
from general.singular_or_plural import sop
from process.general.verslag_pipeline import VerslagCreatingPipeline
from process.input.importing.verslag_from_zip_importer import VerslagFromZipImporter

def report_imports(new_verslagen: list[Verslag], preview=False):
    log_info('Rapportage import:', to_console=True)
    sop_verslagen = sop(len(new_verslagen), "nieuw student-verslag", "nieuwe student-verslagen", False)    
    if len(new_verslagen):
        log_info(f'\t--- {sop_verslagen} --- :')
        for verslag in new_verslagen:
            log_print(f'\t{str(verslag)}')
    log_info(f'\t{len(new_verslagen)} {sop_verslagen} {pva(preview, "te importeren", "geimporteerd")}.', to_console=True)

def process_bbdirectory(directory: str, root_directory: str, storage: AAPAStorage, recursive = True, preview=False)->int:
    def _get_pattern(recursive: bool):
        return '**/*.zip' if recursive else '*.zip'
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start import van map {directory}...', to_console=True)
    importer = VerslagCreatingPipeline(f'Importeren verslagen uit directory {directory}', 
                                       VerslagFromZipImporter(root_directory=root_directory, storage=storage), storage, activity=UndoLog.Action.INPUT)
    first_id = storage.find_max_id('verslagen') + 1
    log_debug(f'first_id: {first_id}')
    (n_processed, n_files) = importer.process(Path(directory).glob(_get_pattern(recursive)), preview=preview)    
    queries: VerslagQueries = storage.queries('verslagen')
    new_verslagen = queries.find_new_verslagen(first_id=first_id)
    report_imports(new_verslagen, preview=preview)
    log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(len(new_verslagen), "nieuw verslag", "nieuwe verslagen")}. In directory: {sop(n_files, "ZIP-bestand", "ZIP-bestanden")})', to_console=True)
    log_debug(MAJOR_DEBUG_DIVIDER)
    return n_processed, n_files      

