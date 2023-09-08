from general.fileutil import from_main_path
from general.log import log_info
from general.preview import Preview
from process.create_forms.create_beoordelings_formulieren import new_create_beoordelingen_files
from process.importing.import_directory import import_directory
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
        geimporteerd = 'importeren' if preview else 'geimporteerd'
        log_info(f'### {n_imported} bestand(en) {geimporteerd} van {input_directory}.', to_console=True)
        n = new_create_beoordelingen_files(storage, get_template_doc(), output_directory, preview=preview)
        verwerkt  = 'klaarzetten voor beoordeling' if preview else 'klaargezet voor beoordeling'        
        log_info(f'### {n} {"aanvragen" if n != 1 else "aanvraag"} {verwerkt} in {output_directory}', to_console=True)
