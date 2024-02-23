from data.classes.undo_logs import UndoLog
from debug.debug import MAJOR_DEBUG_DIVIDER
from general.fileutil import created_directory, test_directory_exists
from main.log import log_debug, log_error, log_info, log_print
from process.forms.creating.verslag_forms_creator import VerslagFormsCreator
from process.general.preview import Preview, pva
from general.singular_or_plural import sop
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.forms.copy_request import CopyAanvraagProcessor
from process.forms.create_diff_file import DifferenceProcessor
from process.forms.creating.aanvraag_form_creator import AanvraagFormCreator
from main.config import config, get_templates
from process.general.verslag_pipeline import VerslagenPipeline
from storage.aapa_storage import AAPAStorage

def init_config():
    config.init('requests', 'form_template',r'template 0.8.docx')
    if template:=config.get('requests', 'form_template'):
        config.set('requests', 'form_template', template.replace('.\\templates\\', ''))
init_config()

def get_template_doc():
    return get_templates(config.get('requests', 'form_template'))

def create_aanvraag_forms(storage: AAPAStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
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
        pipeline = AanvragenPipeline(f'Maken beoordelingsformulieren en kopiëren aanvragen ({output_directory})', 
                                       [AanvraagFormCreator(template_doc, output_directory), 
                                        CopyAanvraagProcessor(output_directory), 
                                        DifferenceProcessor(storage, output_directory)], storage, UndoLog.Action.FORM)
        result = pipeline.process(preview=preview, filter_func=filter_func, output_directory=output_directory) 
    else:
        log_error(f'Output directory "{output_directory}" bestaat niet. Kan geen formulieren aanmaken')
        result = 0
    log_info('--- Einde maken beoordelingsformulieren.')
    return result

def process_aanvraag_forms(storage: AAPAStorage, output_directory, preview=False):
    with Preview(preview, storage, 'requests'):
        log_debug(MAJOR_DEBUG_DIVIDER)
        n_forms = create_aanvraag_forms(storage, get_template_doc(), output_directory, preview=preview)
        log_info(f'### {sop(n_forms, "aanvraag", "aanvragen")} {pva(preview, "klaarzetten", "klaargezet")} voor beoordeling in {output_directory}', to_console=True)
        log_debug(MAJOR_DEBUG_DIVIDER)

def create_verslag_forms(storage: AAPAStorage,filter_func = None, preview=False)->int:
    log_info('--- Maken beoordelingsformulieren voor verslagen  ...', to_console=True)
    pipeline = VerslagenPipeline(f'Maken beoordelingsformulieren verslagen', 
                                    [VerslagFormsCreator(storage)], storage, UndoLog.Action.FORM)
    result = pipeline.process(preview=preview, filter_func=filter_func) 
    log_info('--- Einde maken beoordelingsformulieren.', to_console=True)
    return result

def process_verslag_forms(storage: AAPAStorage, preview=False):
    with Preview(preview, storage, 'requests_reports'):
        log_debug(MAJOR_DEBUG_DIVIDER)
        n_forms = create_verslag_forms(storage, preview=preview)
        log_info(f'### Beoordelingsformulieren voor {sop(n_forms, "verslag", "verslagen")} {pva(preview, "klaarzetten", "klaargezet")} voor beoordeling', to_console=True)
        log_debug(MAJOR_DEBUG_DIVIDER)
