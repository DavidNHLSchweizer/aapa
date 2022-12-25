from general.args import ProcessMode
from general.log import logPrint
from office.beoordeling_formulieren import create_beoordelingen_files
from office.import_data import import_directory
from general.config import config

def init_config():
    config.set_default('requests', 'form_template',r'.\templates\template 0.7.docx')
init_config()

def process_directory(input_directory, storage, output_directory, recursive = True, mode: ProcessMode = ProcessMode.PROCESS):
    (min_id, max_id) = import_directory(input_directory, storage, recursive, mode=mode)
    logPrint(f'### {max(max_id-min_id,0)} bestanden geimporteerd van {input_directory}.')
    n = create_beoordelingen_files(storage, config.get('requests', 'form_template'), output_directory, mode=mode)#, lambda a: a.id >= min_id and a.id <= max_id)
    logPrint(f'### {n} beoordelingsformulieren aangemaakt in {output_directory}')
