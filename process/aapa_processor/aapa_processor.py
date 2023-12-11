from datetime import datetime
from general.fileutil import path_with_suffix
from general.log import log_error, log_info, log_print, log_warning
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.general.import_studenten import import_studenten_XLS
from process.scan.importing.detect_student_from_directory import detect_from_directory
from process.scan.importing.import_verslagen import import_zipfile
from process.undo.undo_processor import undo_last
from process.scan.create_forms.create_diff_file import DifferenceProcessor
# from process.read_grade.history import read_beoordelingen_from_files
from general.config import config
from data.report_aanvragen import report_aanvragen_XLS
from process.mail.mail import process_graded
from process.scan.scan import process_directory, process_forms
from general.args import AAPAConfigOptions, AAPAProcessingOptions, AAPAaction, report_options
from general.versie import banner

class AAPAProcessor:
    def __report_info(self, config_options: AAPAConfigOptions, processing_options: AAPAProcessingOptions):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        log_print(f'CONFIGURATION:\n{tabify(report_options(config_options,processing_options, 1))}')
        log_print(f'OPERATION:\n{tabify(report_options(config_options,processing_options,2))}\n')
    def __create_diff_file(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions):
        DP = DifferenceProcessor(configuration.storage)
        pass
        #TODO: dit bijwerken DP.process_student(configuration.options.diff_file, configuration.output_directory)
    # def __read_history_file(self, configuration: AAPAconfiguration):
    #     if not Path(configuration.options.history_file).is_file():
    #         log_error(f'History file ({configuration.options.history_file}) not found.')
    #     else:
    #         read_beoordelingen_from_files(configuration.options.history_file, configuration.storage)
    def __detect_from_directory(self, directory: str, configuration: AAPAConfiguration, preview = False):
        detect_from_directory(directory, configuration.storage, preview=preview)
    def __import_student_data(self, xls_filename: str, configuration: AAPAConfiguration, preview = False):
        import_studenten_XLS(xls_filename, configuration.storage, preview=preview)   
    def process(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions):
        def must_process(processing_options: AAPAProcessingOptions)->bool:
            if any([a in processing_options.actions for a in {AAPAaction.FULL, AAPAaction.SCAN, AAPAaction.FORM, 
                                                              AAPAaction.MAIL, AAPAaction.UNDO, AAPAaction.NEW, 
                                                              AAPAaction.ZIPIMPORT, AAPAaction.REPORT}]) or\
                processing_options.history_file:
                return True
            return False
        try:
            actions = processing_options.actions
            # print(actions)
            preview = processing_options.preview
            if AAPAaction.INFO in actions:
                self.__report_info(configuration.options, processing_options)
            if processing_options.diff_file:
                self.__create_diff_file(configuration, processing_options)
            if processing_options.detect_dir:
                self.__detect_from_directory(processing_options.detect_dir, configuration, preview=preview)            
            if processing_options.student_file:              
                self.__import_student_data(processing_options.student_file, configuration, preview=preview)
            if not must_process(processing_options):
                return
            if AAPAaction.SCAN in actions or AAPAaction.FULL in actions:
                process_directory(configuration.root, configuration.storage, configuration.output_directory, preview=preview)
            if AAPAaction.ZIPIMPORT in actions: #voorlopig testing123...
                # #checking basedirs
                # for basedir in configuration.storage.basedirs.read_all():
                #     log_print(f'*** DIRECTORY {basedir.year} {basedir.period}')
                #     for directory in Path(basedir.directory).glob('*'):
                #         if directory.is_dir():
                #             print(f'{directory}:{BaseDir.get_student_name(str(directory))}')

                # for student in configuration.storage.studenten.read_all():
                #     parsed = Names.parsed(student.full_name)
                #     if parsed.first_name != student.first_name:
                #         print(f'{student.full_name}: {student.first_name} - {parsed}')
                log_info('not yet implemented')
                        # detect_from_directory(r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022', configuration.storage, preview=preview)    
                # log_print(f'*** DIRECTORY 2022-2023')
                # detect_from_directory(r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023', configuration.storage, preview=preview)    
                # log_print(f'*** DIRECTORY 2023-2024')
                # detect_from_directory(r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024', configuration.storage, preview=preview)    
                # import_zipfile(r'./nova/Gradebook 2023-10-20.zip', 'dummy', storage=configuration.storage, preview=preview)
            if AAPAaction.FORM in actions or AAPAaction.FULL in actions:
                process_forms(configuration.storage, configuration.output_directory, preview=preview)
            #TODO: dit bijwerken if configuration.options.history_file:
            #     self.__read_history_file(configuration)
            if AAPAaction.MAIL in actions or AAPAaction.FULL in actions:
                process_graded(configuration.storage, preview=preview)
            if AAPAaction.UNDO in actions:
                undo_last(configuration.storage, preview=preview)
            if AAPAaction.REPORT in actions:
                report_aanvragen_XLS(configuration.storage, path_with_suffix(processing_options.filename, '.xlsx'))
        except Exception as E:
            log_error(f'Fout bij processing (main): {E}')

class AAPARunnerContext:
    def __init__(self, configuration: AAPAConfiguration, processing_options: AAPAProcessingOptions):
        self.configuration = configuration
        self.processing_options = processing_options
        self.preview = self.needs_preview()
        self.valid = True
    def needs_preview(self)->bool:
        return self.processing_options.preview and not self.processing_options.no_processing()
    def __enter__(self):
        log_info(f'COMMAND LINE OPTIONS:\n{report_options(self.configuration.options, self.processing_options)}')
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

#TODO testing results of rootify on different accounts