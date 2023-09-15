from general.fileutil import created_directory, from_main_path, test_directory_exists
from general.log import log_error, log_info, log_print
from general.preview import Preview, pva
from general.singular_or_plural import sop
from process.general.aanvraag_processor import AanvragenProcessor
from process.scan.create_forms.copy_request import CopyAanvraagProcessor
from process.scan.create_forms.create_diff_file import DifferenceProcessor
from process.scan.create_forms.create_form import FormCreator
from process.scan.importing.import_directory import import_directory
from general.config import config
from data.storage import AAPStorage

def init_config():
    config.init('requests', 'form_template',r'.\templates\template 0.8.docx')
init_config()

def get_template_doc():
    return from_main_path(config.get('requests', 'form_template'))

def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
    log_info('--- Maken beoordelingsformulieren en kopiëren aanvragen ...')
    log_info(f'Formulieren worden aangemaakt in {output_directory}')
    if not preview:
        if created_directory(output_directory):
            log_print(f'Map {output_directory} aangemaakt.')
        exists = test_directory_exists(output_directory)
        if exists:
            storage.add_file_root(str(output_directory))
    else:
        exists = test_directory_exists(output_directory)
    if exists:       
        processor = AanvragenProcessor([FormCreator(template_doc, output_directory), 
                                        CopyAanvraagProcessor(output_directory), 
                                        DifferenceProcessor(storage.aanvragen.read_all(), output_directory)], storage)
        result = processor.process_aanvragen(preview=preview, filter_func=filter_func, output_directory=output_directory) 
    else:
        log_error(f'Output directory "{output_directory}" bestaat niet. Kan geen formulieren aanmaken')
        result = 0
    log_info('--- Einde maken beoordelingsformulieren.')
    return result


def process_directory(input_directory, storage: AAPStorage, output_directory, recursive = True, preview=False):
    with Preview(preview, storage, 'requests'):
        n_imported = import_directory(input_directory, output_directory, storage, recursive, preview=preview)
        print(f'EINDE: {n_imported}')
        log_info(f'### {n_imported} {sop(n_imported, "bestand", "bestanden")} {pva(preview, "importeren", "geimporteerd")} van {input_directory}.', to_console=True)
        n_forms = create_beoordelingen_files(storage, get_template_doc(), output_directory, preview=preview)
        log_info(f'### {n_forms} {sop(n_forms, "aanvraag", "aanvragen")} {pva(preview, "klaarzetten", "klaargezet")} voor beoordeling in {output_directory}', to_console=True)
