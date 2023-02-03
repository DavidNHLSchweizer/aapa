from general.log import logPrint
from general.preview import Preview
from process.create_forms.beoordeling_formulieren import create_beoordelingen_files
from process.importing.import_data import import_directory
from general.config import config
from data.storage import AAPStorage

def init_config():
    config.set('requests', 'form_template',r'.\templates\template 0.8.docx')
init_config()

def process_directory(input_directory, storage: AAPStorage, output_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests'):
        (min_id, max_id) = import_directory(input_directory, storage, recursive, preview=preview)
        geimporteerd = 'importeren' if preview else 'geimporteerd'
        logPrint(f'### {max(max_id-min_id+1,0)} bestand(en) {geimporteerd} van {input_directory}.')
        n = create_beoordelingen_files(storage, config.get('requests', 'form_template'), output_directory, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        logPrint(f'### {n} beoordelingsformulier(en) {aangemaakt} in {output_directory}')