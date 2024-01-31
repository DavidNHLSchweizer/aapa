from datetime import datetime
from data.storage.queries.student_directories import StudentDirectoryQueries
from general.fileutil import path_with_suffix
from general.log import log_error, log_info, log_print, log_warning
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.input.importing.import_bb_directory import import_bbdirectory
from process.migrate.import_basedir import import_basedirs_XLS
from process.migrate.import_studenten import import_studenten_XLS
from process.report.report_student_directory import StudentDirectoryReporter
from process.input.importing.detect_student_from_directory import detect_from_directory
from process.undo.undo_processor import undo_last
from process.input.create_forms.create_diff_file import DifferenceProcessor
from data.report_aanvragen import report_aanvragen_XLS
from process.mail.mail import process_graded
from process.input.scan import process_directory, process_excel_file, process_forms
from general.args import AAPAOptions, AAPAOtherOptions, AAPAProcessingOptions, AAPAaction, report_options
from general.versie import banner
from general.config import config

class AAPAProcessor:
    def __report_info(self, options: AAPAOptions):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        log_print(f'CONFIGURATION:\n{tabify(report_options(options, 1))}')
        log_print(f'OPERATION:\n{tabify(report_options(options,2))}\n')
    def __create_diff_file(self, configuration: AAPAConfiguration, other_options: AAPAOtherOptions):
        DP = DifferenceProcessor(configuration.storage)
        pass
        #TODO: dit bijwerken DP.process_student(configuration.options.diff_file, configuration.output_directory)
    # def __read_history_file(self, configuration: AAPAconfiguration):
    #     if not Path(configuration.options.history_file).is_file():
    #         log_error(f'History file ({configuration.options.history_file}) not found.')
    #     else:
    #         read_beoordelingen_from_files(configuration.options.history_file, configuration.storage)
    def __detect_from_directory(self, directory: str, configuration: AAPAConfiguration, preview = False):
        detect_from_directory(directory, configuration.storage, migrate_dir=configuration.config_options.migrate_dir, preview=preview)
    def __import_student_data(self, xls_filename: str, configuration: AAPAConfiguration, preview = False):
        import_studenten_XLS(xls_filename, configuration.storage, migrate_dir=configuration.config_options.migrate_dir, preview=preview)   
    def __import_basedir_data(self, xls_filename: str, configuration: AAPAConfiguration, preview = False):
        import_basedirs_XLS(xls_filename, configuration.storage, migrate_dir=configuration.config_options.migrate_dir, preview=preview)   
   
    def __process_other_options(self, configuration: AAPAConfiguration, other_options: AAPAOtherOptions, preview = False):        
        if other_options.diff_file:
                self.__create_diff_file(configuration, other_options)
        if other_options.detect_dir:
            self.__detect_from_directory(other_options.detect_dir, configuration, preview=preview)            
            StudentDirectoryReporter().report(configuration.storage)
        if other_options.student_file:              
            self.__import_student_data(other_options.student_file, configuration, preview=preview)
        if other_options.basedir_file:              
            self.__import_basedir_data(other_options.basedir_file, configuration, preview=preview)
        if other_options.history_file:              
            raise ValueError(f'#NOTIMPLEMENTED: HISTORY {other_options.history_file}')

    def process(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions, other_options: AAPAOtherOptions):
        try:            
            actions = processing_options.actions
            # print(actions)
            preview = processing_options.preview
            if AAPAaction.INFO in actions:
                self.__report_info(AAPAOptions(config_options=configuration.config_options, processing_options=processing_options, other_options=other_options))
            if not other_options.no_processing():
                    self.__process_other_options(configuration, other_options, preview=preview)      
            # with open('overzichtje.csv', mode="w", encoding='utf-8') as file:                  
            #     for student in configuration.storage.find_all('studenten'):
            #         queries:StudentDirectoryQueries = configuration.storage.queries('student_directories')  
            #         stud_dir = queries.find_student_dir(student)
            #         file.write(";".join([str(student.id), student.full_name, student.stud_nr, str(student.status), encode_path(stud_dir.directory)])+"\n")
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
                # import_zipfile(r'./nova/Gradebook 2023-10-20.zip', 'dummy', storage=configuration.storage, preview=preview)
            if AAPAaction.FORM in actions or AAPAaction.FULL in actions:
                if AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN in processing_options.processing_mode:
                    process_forms(configuration.storage, configuration.output_directory, preview=preview)
                if AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN in processing_options.processing_mode:
                    log_info(f'BBZIP {configuration.config_options.bbinput_directory}: not yet implemented', to_console=True)
            #TODO: dit bijwerken if configuration.options.history_file:
            #     self.__read_history_file(configuration)
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
    def __init__(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions, other_options: AAPAOtherOptions):
        self.configuration = configuration
        self.processing_options = processing_options
        self.other_options = other_options
        self.preview = self.needs_preview()
        self.valid = True
    @property
    def options(self)->AAPAOptions:
        return AAPAOptions(config_options=self.configuration.config_options, 
                           processing_options=self.processing_options,
                           other_options=self.other_options)
    def needs_preview(self)->bool:
        if not self.processing_options.preview:
            return False
        else:
            return not self.processing_options.no_processing() or not self.other_options.no_processing()
    def __enter__(self):
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

