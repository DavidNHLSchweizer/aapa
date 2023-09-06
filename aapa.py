from pathlib import Path
import tkinter.messagebox as tkimb
import tkinter.filedialog as tkifd
from general.fileutil import from_main_path, path_with_suffix
from general.log import init_logging, logError, logInfo, logWarning
from general.preview import Preview
from process.create_forms.difference import DifferenceProcessor
from process.read_grade.history import read_beoordelingen_from_files
from process.graded_requests import process_graded
from general.config import config
from data.report_data import report_aanvragen_XLS, report_aanvragen_console
from process.initialize import initialize_database, initialize_storage
from process.scan import process_directory
from general.args import AAPAaction, AAPAoptions, get_arguments, report_options
from general.versie import banner

DEFAULTDATABASE = 'aapa.db'
LOGFILENAME = 'aapa.log'
def init_config():
    config.init('configuration', 'database', DEFAULTDATABASE)
    config.init('configuration', 'root', '')
    config.init('configuration', 'forms', '')
init_config()

def verifyRecreate():
    return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

class AAPAconfiguration:
    def __init__(self, options: AAPAoptions):
        if options.config_file:
            config_file = path_with_suffix(options.config_file, '.ini')
            if not Path(config_file).is_file():
                logError(f'Alternatieve configuratiefile ({config_file}) niet gevonden.')
            config.read(config_file)
            logInfo(f'Alternative configuratie file {config_file} geladen.')
        self.options = options
        self.actions = options.actions
        self.preview = options.preview
    def get_database_name(self):
        if self.options.database_file:
            database = self.options.database_file
            config.set('configuration', 'database', database) 
        else:
            database = config.get('configuration','database') 
        return from_main_path(path_with_suffix(database, '.db'))
    def __initialize_database(self):
        database = self.get_database_name()
        recreate = (AAPAaction.NEW in self.actions and (not Path(database).is_file() or verifyRecreate()))
        self.database = initialize_database(database, recreate)
        self.storage  = initialize_storage(self.database)
    def __initialize_directories(self):        
        self.root = self.__get_directory(self.options.root_directory, 'root','Root directory voor aanvragen', True)
        self.forms_directory = self.__get_directory(self.options.forms_directory, 'forms', 'Directory voor beoordelingsformulieren')
    def __get_directory(self, option_value, config_name, title, mustexist=False):
        config_value = config.get('configuration', config_name)
        if (option_value is not None and not option_value) or (not config_value):
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
    def initialize(self):
        self.__initialize_database()
        self.__initialize_directories()
        if self.options.history_file is not None:
            self.options.history_file = path_with_suffix(self.__get_history_file(self.options.history_file), '.xlsx')

class AAPAprocessor:
    def __report_info(self, options):
        def tabify(s):
            return '\t' + s.replace('\n', '\n\t')
        print(f'CONFIGURATION:\n{tabify(report_options(options,1))}')
        print(f'OPERATION:\n{tabify(report_options(options,2))}\n')
    def __create_diff_file(self, configuration: AAPAconfiguration):
        DP = DifferenceProcessor(configuration.storage)
        DP.process_student(configuration.options.diff_file, configuration.forms_directory)
    def __read_history_file(self, configuration: AAPAconfiguration):
        if not Path(configuration.options.history_file).is_file():
            logError(f'History file ({configuration.options.history_file}) not found.')
        else:
            read_beoordelingen_from_files(configuration.options.history_file, configuration.storage)
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
                process_directory(configuration.root, configuration.storage, configuration.forms_directory, preview=configuration.preview)
            if configuration.options.history_file:
                self.__read_history_file(configuration)
            if AAPAaction.MAIL in configuration.actions or AAPAaction.FULL in configuration.actions:
                process_graded(configuration.storage, preview=configuration.preview)
            if AAPAaction.REPORT in configuration.actions:
                report_aanvragen_XLS(configuration.storage, path_with_suffix(configuration.options.filename, '.xlsx'))
        except Exception as E:
            logError(f'Fout bij processing: {E}')

class AAPA:
    def __init__(self, options: AAPAoptions):
        self.configuration = AAPAconfiguration(options)
    def process(self):
        self.configuration.initialize()        
        with Preview(self.configuration.preview, self.configuration.storage, 'main'):
            AAPAprocessor().process(self.configuration)
        logInfo('Ready.')

if __name__=='__main__':
    print(banner())
    init_logging(LOGFILENAME)
    logInfo('+++ AAPA started +++')
    aapa = AAPA(get_arguments())
    logInfo(f'COMMAND LINE OPTIONS:\n{report_options(aapa.configuration.options)}')
    aapa.process() 
    logInfo('+++ AAPA stopped +++\n')

#TODO testing results of rootify on different accounts