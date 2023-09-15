from datetime import datetime
from general.fileutil import path_with_suffix
from general.log import log_error, log_info, log_print
from process.aapa_processor.aapa_config import AAPAconfiguration
from process.scan.create_forms.create_diff_file import DifferenceProcessor
# from process.read_grade.history import read_beoordelingen_from_files
from general.config import config
from data.report_data import report_aanvragen_XLS
from process.mail.mail import process_graded
from process.scan.scan import process_directory
from general.args import AAPAaction, AAPAoptions, get_arguments, report_options
from general.versie import banner

class AAPAProcessor:
    def __report_info(self, options):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        log_print(f'CONFIGURATION:\n{tabify(report_options(options,1))}')
        log_print(f'OPERATION:\n{tabify(report_options(options,2))}\n')
    def __create_diff_file(self, configuration: AAPAconfiguration):
        DP = DifferenceProcessor(configuration.storage)
        pass
        #TODO: dit bijwerken DP.process_student(configuration.options.diff_file, configuration.output_directory)
    # def __read_history_file(self, configuration: AAPAconfiguration):
    #     if not Path(configuration.options.history_file).is_file():
    #         log_error(f'History file ({configuration.options.history_file}) not found.')
    #     else:
    #         read_beoordelingen_from_files(configuration.options.history_file, configuration.storage)
    def process(self, configuration: AAPAconfiguration):
        def must_process(options: AAPAoptions)->bool:
            if any([a in options.actions for a in [AAPAaction.FULL, AAPAaction.MAIL, AAPAaction.SCAN, AAPAaction.NEW, AAPAaction.REPORT]]) or\
                options.history_file:
                return True
            return False
        try:
            if AAPAaction.INFO in configuration.options.actions:
                self.__report_info(configuration.options)
            if configuration.options.diff_file:
                self.__create_diff_file(configuration)
            if not must_process(configuration.options):
                return
            if AAPAaction.SCAN in configuration.actions or AAPAaction.FULL in configuration.actions:
                process_directory(configuration.root, configuration.storage, configuration.output_directory, preview=configuration.preview)
            #TODO: dit bijwerken if configuration.options.history_file:
            #     self.__read_history_file(configuration)
            if AAPAaction.MAIL in configuration.actions or AAPAaction.FULL in configuration.actions:
                process_graded(configuration.storage, preview=configuration.preview)
            if AAPAaction.REPORT in configuration.actions:
                report_aanvragen_XLS(configuration.storage, path_with_suffix(configuration.options.filename, '.xlsx'))
        except Exception as E:
            log_error(f'Fout bij processing: {E}')

class AAPARunnerContext:
    def __init__(self, options: AAPAoptions):
        self.options = options
    def __enter__(self):
        log_info(f'COMMAND LINE OPTIONS:\n{report_options(self.options)}')
        log_print(banner())
        log_info(f'+++ AAPA started +++ {datetime.strftime(datetime.now(), "%d-%m-%Y, %H:%M:%S")}', to_console=True)
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        log_info('Ready.')
        log_info(f'+++ AAPA stopped +++ {datetime.strftime(datetime.now(), "%d-%m-%Y, %H:%M:%S")}\n', to_console=True)

#TODO testing results of rootify on different accounts