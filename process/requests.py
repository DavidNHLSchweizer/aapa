from office.beoordeling_formulieren import create_beoordelingen_files
from office.import_data import import_directory
from general.config import config

def init_config():
    config.set_default('requests', 'form_template',r'.\templates\template 0.7.docx')
init_config()

def process_directory(input_directory, storage, output_directory):
    (min_id, max_id) = import_directory(input_directory, storage)
    create_beoordelingen_files(storage, config.get('requests', 'form_template'), output_directory, lambda a: a.id >= min_id and a.id <= max_id)
