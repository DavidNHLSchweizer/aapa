from general.args import ProcessMode
from general.log import logPrint
from office.beoordeling_formulieren import create_beoordelingen_files
from office.import_data import import_directory
from general.config import config
from data.storage import AAPStorage

def init_config():
    config.set_default('requests', 'form_template',r'.\templates\template 0.7.docx')
init_config()

def process_directory(input_directory, storage: AAPStorage, output_directory, recursive = True, preview=False):
    if preview:
        storage.database.disable_commit()
        print('*** PREVIEW ONLY ***')
    try:
        (min_id, max_id) = import_directory(input_directory, storage, recursive, preview=preview)
        geimporteerd = 'importeren' if preview else 'geimporteerd'
        logPrint(f'### {max(max_id-min_id+1,0)} bestand(en) {geimporteerd} van {input_directory}.')
        n = create_beoordelingen_files(storage, config.get('requests', 'form_template'), output_directory, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        logPrint(f'### {n} beoordelingsformulier(en) {aangemaakt} in {output_directory}')

    finally:
        if preview:
            storage.database.rollback()
            storage.database.enable_commit()
            print('*** end PREVIEW ONLY ***')
