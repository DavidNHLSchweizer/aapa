from general.fileutil import from_main_path
from general.log import log_print
from general.preview import Preview
from process.create_forms.beoordeling_formulieren import create_beoordelingen_files
from process.importing.import_data import import_directory
from general.config import config
from data.storage import AAPStorage

def init_config():
    config.init('requests', 'form_template',r'.\templates\template 0.8.docx')
init_config()

def get_template_doc():
    return from_main_path(config.get('requests', 'form_template'))

def process_directory(input_directory, storage: AAPStorage, output_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests'):
        (min_id, max_id) = import_directory(input_directory, storage, recursive, preview=preview)
        geimporteerd = 'importeren' if preview else 'geimporteerd'
        log_print(f'### {max(max_id-min_id+1,0)} bestand(en) {geimporteerd} van {input_directory}.')
        n = create_beoordelingen_files(storage, get_template_doc(), output_directory, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        log_print(f'### {n} beoordelingsformulier(en) {aangemaakt} in {output_directory}')
