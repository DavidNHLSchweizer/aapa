from pathlib import Path
import sys
import tkinter.messagebox as tkimb
import tkinter.filedialog as tkifd
from general.fileutil import path_with_suffix
from general.log import init_logging, logError, logInfo
from general.preview import Preview
from office.cleanup import cleanup_files
from office.history import read_beoordelingen_from_files
from process.graded_requests import process_graded
from general.config import config
from office.report_data import report_aanvragen_XLS, report_aanvragen_console
from process.database import initialize_database, initialize_storage
from process.requests import process_directory
from data.aanvraag_info import AanvraagBeoordeling
from general.args import AAPAoptions, Initialize, ProcessMode, get_arguments, report_options

def init_config():
    config.set_default('configuration', 'database', 'aapa.db')
    config.set_default('configuration', 'root', r'.\aanvragen')
    config.set_default('configuration', 'forms', r'.\aanvragen\forms')
init_config()

def verifyRecreate():
    return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

class AAPA:
    def __init__(self, options: AAPAoptions):
        if options.info:
            self.__report_info(options)
        logInfo(f'COMMAND LINE OPTIONS:\n{report_options(options)}')
        self.options = options
        self.mode    = options.mode
        self.cleanup = options.clean
        self.preview = options.preview
        self.report    = options.report
    def __report_info(self, options):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        print(f'CONFIGURATION:\n{tabify(report_options(options,1))}')
        print(f'OPERATION:\n{tabify(report_options(options,2))}\n')

    def get_database_name(self):
        if self.options.database:
            database = self.options.database
            config.set('configuration', 'database', database) 
        else:
            database = config.get('configuration','database') 
        return path_with_suffix(database, '.db').resolve()
    def __initialize_database(self, options: AAPAoptions):
        recreate =  (options.initialize == Initialize.INIT and verifyRecreate()) or options.initialize == Initialize.INIT_FORCE
        self.database = initialize_database(self.get_database_name(), recreate)
        self.storage  = initialize_storage(self.database)
    def __initialize_directories(self, options: AAPAoptions):        
        self.root = self.__get_directory(options.root, 'root','Root directory voor aanvragen', True)
        self.forms_directory = self.__get_directory(options.forms, 'forms', 'Directory voor beoordelingsformulieren')
    def __get_directory(self, option_value, config_name, title, mustexist=False):
        if option_value is not None and not option_value:
            result = tkifd.askdirectory(mustexist=mustexist, title=title)
        else:
            result = option_value
        if result and result != config.get('configuration', config_name):
            setattr(self, config_name, result)
            config.set('configuration', config_name, result)
        else:
            result = config.get('configuration', config_name)
        if result:
            return Path(result).resolve()
        else:
            return None
    def __get_history_file(self, option_history):
        if option_history:
            return option_history
        else:
            return tkifd.askopenfilename(initialfile=option_history,initialdir='.', defaultextension='.xlsx')
    def __init_process(self):
        self.__initialize_database(self.options)
        self.__initialize_directories(self.options)
        if self.options.history is not None:
            self.options.history = path_with_suffix(self.__get_history_file(self.options.history), '.xlsx')
    def process(self):
        self.__init_process()
        with Preview(self.preview, self.storage, 'main'):
            try:
                if self.mode != ProcessMode.NONE:
                    if self.root and self.mode != ProcessMode.MAIL:
                        process_directory(self.root, self.storage, self.forms_directory, preview=self.preview)
                    if self.options.history:
                        if not Path(self.options.history).is_file():
                            logError(f'History file ({self.options.history}) not found.')
                        else:
                            read_beoordelingen_from_files(self.options.history, self.storage)
                    if self.mode != ProcessMode.SCAN:
                        process_graded(self.storage, preview=self.preview)
                if self.cleanup:
                    cleanup_files(self.storage, preview=self.preview)
                if self.report is not None:
                    if self.report:
                        report_aanvragen_XLS(self.storage, path_with_suffix(self.report, '.xlsx'))
                    else:
                        report_aanvragen_console(self.storage)
            except Exception as E:
                logError(f'Fout bij processing: {E}')

        logInfo('Ready.')
    @staticmethod
    def banner():
        return f'AAPA-Afstudeer Aanvragen Proces Applicatie  versie {config.get("versie", "versie")}'

if __name__=='__main__':
    print(AAPA.banner())
    aapa = AAPA(get_arguments())
    init_logging(aapa.get_database_name())
    logInfo('+++ AAPA started +++')
    aapa.process() 
    logInfo('+++ AAPA stopped +++')

#TODO testing results of rootify on different accounts