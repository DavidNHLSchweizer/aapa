from general.fileutil import from_main_path
from general.log import log_info
from general.preview import Preview, pva
from general.singular_or_plural import sop
from process.scan.create_forms.pipeline.create_forms import create_beoordelingen_files
from process.scan.importing.import_directory import import_directory
from general.config import config
from data.storage import AAPStorage

def init_config():
    config.init('requests', 'form_template',r'.\templates\template 0.8.docx')
init_config()

def get_template_doc():
    return from_main_path(config.get('requests', 'form_template'))

def process_directory(input_directory, storage: AAPStorage, output_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests'):
        n_imported = import_directory(input_directory, output_directory, storage, recursive, preview=preview)
        log_info(f'### {n_imported} {sop(n_imported, "bestand", "bestanden")} {pva(preview, "importeren", "geimporteerd")} van {input_directory}.', to_console=True)
        n_forms = create_beoordelingen_files(storage, get_template_doc(), output_directory, preview=preview)
        log_info(f'### {n_forms} {sop(n_forms, "aanvraag", "aanvragen")} {pva(preview, "klaarzetten", "klaargezet")} voor beoordeling in {output_directory}', to_console=True)
