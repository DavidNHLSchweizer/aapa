from datetime import datetime
from general.fileutil import path_with_suffix
from main.log import log_error, log_info, log_print, log_warning
from process.main.aapa_config import AAPAConfiguration
from process.input.importing.import_bb_directory import import_bbdirectory
from process.undo.undo_processor import undo_last
from process.general.report_aanvragen import report_aanvragen_XLS
from process.mail.mail import process_graded
from process.input.scan import process_directory, process_excel_file, process_forms
from main.args import AAPAOptions, AAPAProcessingOptions, AAPAaction, report_options
from main.versie import banner
from main.config import config

class AAPAProcessor:
    def __report_info(self, options: AAPAOptions):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        log_print(f'CONFIGURATION:\n{tabify(report_options(options, 1))}')
        log_print(f'OPERATION:\n{tabify(report_options(options,2))}\n')
    def process(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions):
        try:            
            actions = processing_options.actions
            preview = processing_options.preview
            if AAPAaction.INFO in actions:
                self.__report_info(AAPAOptions(config_options=configuration.config_options, processing_options=processing_options))
            if processing_options.no_processing():
                return            
            if AAPAaction.INPUT in actions or AAPAaction.FULL in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    if AAPAProcessingOptions.INPUTOPTIONS.EXCEL in processing_options.input_options and configuration.config_options.excel_in:
                        process_excel_file(configuration.config_options.excel_in, configuration.storage, configuration.root, preview=preview)
                    if AAPAProcessingOptions.INPUTOPTIONS.SCAN in processing_options.input_options and (old_root := config.get('configuration', 'scanroot')): 
                        process_directory(old_root, configuration.storage, configuration.output_directory, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN in processing_options.processing_mode: 
                    import_bbdirectory(configuration.config_options.bbinput_directory, configuration.config_options.root_directory, configuration.storage, preview=preview)                    
            if AAPAaction.FORM in actions or AAPAaction.FULL in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    process_forms(configuration.storage, configuration.output_directory, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN in processing_options.processing_mode:
                    log_info(f'BBZIP {configuration.config_options.bbinput_directory}: not yet implemented', to_console=True)
            if AAPAaction.MAIL in actions or AAPAaction.FULL in actions:
                process_graded(configuration.storage, preview=preview)
            if AAPAaction.UNDO in actions:
                undo_last(configuration.storage, preview=preview)
            if AAPAaction.REPORT in actions:
                report_aanvragen_XLS(configuration.storage, 
                                     path_with_suffix(configuration.config_options.report_filename, '.xlsx'))
        except Exception as E:
            log_error(f'Fout bij processing (main): {E}')

class AAPARunnerContext:
    def __init__(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions, message=None):
        self.configuration = configuration
        self.processing_options = processing_options
        self.preview = self.needs_preview()
        self.valid = True
        self.message=message
    @property
    def options(self)->AAPAOptions:
        return AAPAOptions(config_options=self.configuration.config_options, 
                           processing_options=self.processing_options
                           )
    def needs_preview(self)->bool:
        if not self.processing_options.preview:
            return False
        else:
            return not self.processing_options.no_processing() 
    def __enter__(self):
        if self.message:
            log_info(self.message, to_console=True)
        log_info(f'COMMAND LINE OPTIONS:\n{report_options(self.options)}')
        log_print(banner())
        log_info(f'+++ AAPA started +++ {datetime.strftime(datetime.now(), "%d-%m-%Y, %H:%M:%S")}', to_console=True)
        self.valid = True
        if not (self.configuration.initialize(self.processing_options)):
            self.valid = False
            if AAPAaction.INFO in self.processing_options.actions:
                log_warning(f'{self.configuration.validation_error}\nKan AAPA niet initialiseren.')
            else:
                log_error(f'{self.configuration.validation_error}\nKan AAPA niet initialiseren.')
                return None
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        log_info('Ready.')
        log_info(f'+++ AAPA stopped +++ {datetime.strftime(datetime.now(), "%d-%m-%Y, %H:%M:%S")}\n', to_console=True)

