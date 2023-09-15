from general.fileutil import created_directory, test_directory_exists
from general.log import log_error, log_info, log_print
from process.general.aanvraag_processor import AanvragenProcessor
from process.scan.create_forms.copy_request import CopyAanvraagProcessor
from process.scan.create_forms.create_form import FormCreator
from process.scan.create_forms.create_diff_file import DifferenceProcessor
from data.storage import AAPStorage


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
