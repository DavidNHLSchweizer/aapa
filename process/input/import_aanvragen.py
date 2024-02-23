from debug.debug import MAJOR_DEBUG_DIVIDER
from general.singular_or_plural import sop
from main.log import log_debug, log_info, log_warning
from process.general.preview import Preview, pva
from process.input.importing.import_directory_aanvragen import import_directory
from process.input.importing.import_excel_aanvragen import import_excel_file
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries


def check_root_directory(root_directory: str, storage: AAPAStorage):
    queries:BaseDirQueries = storage.queries('base_dirs')
    if not queries.is_basedir(root_directory):
        storage.add_basedir(root_directory) 
        log_warning(f'Basis directory {root_directory} is nog niet bekend.\nWordt geinitialiseerd met default waarden. \nHet is ESSENTIEEL om dit nog in de database aan te passen!')

def process_excel_file(excel_filename, storage: AAPAStorage, root_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests_excel'):
        log_debug(MAJOR_DEBUG_DIVIDER)
        check_root_directory(root_directory,storage)
        n_imported,_ = import_excel_file(excel_filename, root_directory, storage, preview=preview)
        log_info(f'### {sop(n_imported, "aanvraag", "aanvragen")} {pva(preview, "importeren", "geimporteerd")} van {excel_filename}.', to_console=True)
        log_debug(MAJOR_DEBUG_DIVIDER)

def scan_aanvraag_directory(input_directory, storage: AAPAStorage, output_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests_files'):
        log_debug(MAJOR_DEBUG_DIVIDER)
        check_root_directory(input_directory,storage)
        n_imported,_ = import_directory(input_directory, output_directory, storage, recursive, preview=preview)
        log_info(f'### {sop(n_imported, "aanvraag", "aanvragen")} {pva(preview, "importeren", "geimporteerd")} van {input_directory}.', to_console=True)
        log_debug(MAJOR_DEBUG_DIVIDER)

