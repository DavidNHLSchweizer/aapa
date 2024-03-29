from datetime import datetime
from general.fileutil import path_with_suffix
from main.log import log_error, log_info, log_print, log_warning, not_implemented
from process.general.const import AAPAaction
from process.input.import_aanvragen import scan_aanvraag_directory, process_excel_file
from process.main.aapa_config import AAPAConfiguration
from process.input.import_verslagen import process_bbdirectory
from process.general.report_aanvragen import report_aanvragen_XLS
from process.mail.mail import process_graded
from process.forms.forms import process_aanvraag_forms, process_verslag_forms
from main.options import AAPAOptions, AAPAProcessingOptions, report_options
from main.versie import banner
from main.config import config
from process.undo.undo import undo_last_aanvragen, undo_last_verslagen
from storage.aapa_storage import AAPAStorage

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
                        process_excel_file(configuration.config_options.excel_in, configuration.storage, configuration.root, preview=preview, last_excel_id=processing_options.last_id)
                    if AAPAProcessingOptions.INPUTOPTIONS.SCAN in processing_options.input_options and (old_root := config.get('configuration', 'scanroot')): 
                        scan_aanvraag_directory(old_root, configuration.storage, configuration.output_directory, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN in processing_options.processing_mode: 
                    process_bbdirectory(configuration.config_options.bbinput_directory, configuration.config_options.root_directory, configuration.storage, preview=preview)                    
            if AAPAaction.FORM in actions or AAPAaction.FULL in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    process_aanvraag_forms(configuration.storage, configuration.output_directory, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN in processing_options.processing_mode:
                    process_verslag_forms(configuration.storage, preview=preview)
            if AAPAaction.MAIL in actions or AAPAaction.FULL in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    process_graded(configuration.storage, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN in processing_options.processing_mode:
                    not_implemented(f'Mail is niet geimmplementeerd voor verslagen')
            if AAPAaction.UNDO in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    undo_last_aanvragen(configuration.storage, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN in processing_options.processing_mode:
                    undo_last_verslagen(configuration.storage, preview=preview)
            if AAPAaction.REPORT in actions:
                report_aanvragen_XLS(configuration.storage, 
                                     path_with_suffix(configuration.config_options.report_filename, '.xlsx'))
        except Exception as E:
            log_error(f'Fout bij processing (main): {E}')

class AAPARunnerContext:
    """ AAPA context: provides access to storage and options. 
    
        By using this as a ContextManager you can access the storage and options.
        AAPARunnerContext takes care of all initialization. 
        
        If the context is valid, (valid property) everything is initialized correctly.

        attributes
        ----------
        configuration: AAPAConfiguration object. Contains storage, direct access to database, and config options.
        processing_options: AAPAProcessing object. The processing options.
        preview: if True it should be a preview run 
            #TODO: this could probably be included in the __enter__ method. Preview is now done separately.
        valid: Check validity. If valid is False, there was a problem initializing.     
             
        example use
        ----------- 
            with AAPARunnerContext(configuration, processing_options) as context:
            
    """
    def __init__(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions, plugin=False, message=None):
        """ 
        parameters
        ---------- 
        configuration: the configuration object, based on the AAPAConfigOptions. 
            Contains database and key directories.
        processing_options: AAPAProcessingOptions.
            Contains actions and options for processing. 
        options (property): AAPAOptions object combining config_options and processing_options.
        message: optional message. displayed and logged at start of contextmanager.
        
        """
        self.configuration = configuration
        self.processing_options = processing_options
        self.plugin=plugin
        self.preview = self.needs_preview()
        self.valid = True
        self._message=message
    @property
    def storage(self)->AAPAStorage:
        return self.configuration.storage
    @property
    def options(self)->AAPAOptions:
        return AAPAOptions(config_options=self.configuration.config_options, 
                           processing_options=self.processing_options
                           )
    def needs_preview(self)->bool:
        if not self.processing_options.preview:
            return False
        else:
            return not self.processing_options.no_processing(self.plugin) 
    def __enter__(self):
        if self._message:
            log_info(self._message, to_console=True)
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

