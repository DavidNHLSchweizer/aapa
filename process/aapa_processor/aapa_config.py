from pathlib import Path
import tkinter.messagebox as tkimb
import tkinter.filedialog as tkifd
from general.fileutil import created_directory, file_exists, from_main_path, path_with_suffix, test_directory_exists
from general.log import log_error, log_info, log_print
from general.config import config
from process.aapa_processor.initialize import initialize_database, initialize_storage
from general.args import AAPAaction, AAPAoptions

DEFAULTDATABASE = 'aapa.db'
LOGFILENAME = 'aapa.log'
def init_config():
    config.init('configuration', 'database', DEFAULTDATABASE)
    config.init('configuration', 'root', '')
    config.init('configuration', 'output', '')  
init_config()

def verifyRecreate():
    return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

class AAPAconfiguration:
    def __init__(self, options: AAPAoptions):
        self.validation_error = None
        if options.config_file:
            config_file = path_with_suffix(options.config_file, '.ini')
            if not Path(config_file).is_file():
                log_error(f'Alternatieve configuratiefile ({config_file}) niet gevonden.')
            config.read(config_file)
            log_info(f'Alternative configuratie file {config_file} geladen.')
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
    def __initialize_database(self)->bool:
        database = self.get_database_name()
        recreate = (AAPAaction.NEW in self.actions and (not Path(database).is_file() or self.options.force or verifyRecreate()))
        self.database = initialize_database(database, recreate)
        self.storage  = initialize_storage(self.database)
        if not self.database or not self.database.connection:
            self.validation_error = f'Database {database} gecorrumpeerd of ander probleem met database'
            return False
        return True
    def __prepare_storage_roots(self):
        # initialize file roots BEFORE processing to cover for cases where aanvraagformulieren 
        # (stored in the output_directory) are created with the wrong root
        # this will cause problems later on
        if not self.preview:
            self.storage.add_file_root(str(self.root))
        if created_directory(self.output_directory):
            log_print(f'Map {self.output_directory} aangemaakt.')
        self.storage.add_file_root(str(self.output_directory))
    def __initialize_directories(self)->bool:        
        self.root = self.__get_directory(self.options.root_directory, 'root','Root directory voor aanvragen', True)
        if not self.root or not test_directory_exists(self.root):
            self.validation_error = f'Root directory "{self.root}" voor aanvragen niet ingesteld of bestaat niet'
            return False
        self.output_directory = self.__get_directory(self.options.output_directory, 'output', 'Directory voor nieuwe beoordelingsformulieren')
        if not self.output_directory:
            self.validation_error = f'Output directory "{self.output_directory}" voor aanvragen niet ingesteld'
            return False
        self.__prepare_storage_roots()
        return True
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
    def initialize(self)->bool:
        return self.__initialize_database() and self.__initialize_directories()
        # if self.options.history_file is not None:
        #     self.options.history_file = path_with_suffix(self.__get_history_file(self.options.history_file), '.xlsx')
        return True
