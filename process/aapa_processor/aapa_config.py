from enum import Enum, auto
from pathlib import Path
import tkinter.messagebox as tkimb
import tkinter.filedialog as tkifd
from data.roots import decode_onedrive, encode_onedrive
from general.fileutil import created_directory, file_exists, from_main_path, path_with_suffix, test_directory_exists
from general.log import log_error, log_info, log_print, log_warning
from general.config import ValueConvertor, config
from process.aapa_processor.initialize import initialize_database, initialize_storage
from general.args import AAPAConfigOptions, AAPAProcessingOptions, AAPAaction

class OnedrivePathValueConvertor(ValueConvertor):
    def get(self, section_key: str, key_value: str, **kwargs)->str:
        if (section := self._parser[section_key]) is not None:
            return decode_onedrive(section.get(key_value, **kwargs))
        return None
    def set(self, section_key: str, key_value: str, value: object):
        if (section := self._parser[section_key]) is not None:
            section[key_value] = encode_onedrive(str(value))

DEFAULTDATABASE = 'aapa.db'
LOGFILENAME = 'aapa.log'
def init_config():
    config.init('configuration', 'database', DEFAULTDATABASE)
    config.register('configuration', 'root', OnedrivePathValueConvertor)
    config.register('configuration', 'output', OnedrivePathValueConvertor)
    config.register('configuration', 'input', OnedrivePathValueConvertor)
    config.init('configuration', 'root', '')
    config.init('configuration', 'output', '')  
    config.init('configuration', 'input', '')  
init_config()

def verifyRecreate():
    return tkimb.askyesno('Vraagje', 'Alle data wordt verwijderd. Is dat echt wat je wilt?', default = tkimb.NO, icon=tkimb.WARNING) 

class AAPAConfiguration:
    class PART(Enum):
        DATABASE = auto()
        DIRECTORIES = auto()     
        BOTH    = auto()   
    def __init__(self, config_options: AAPAConfigOptions):
        self.validation_error = None
        self.storage  = None
        self.database = None
        if config_options.config_file:
            config_file = path_with_suffix(config_options.config_file, '.ini')
            if not Path(config_file).is_file():
                log_error(f'Alternatieve configuratiefile ({config_file}) niet gevonden.')
            config.read(config_file)
            log_info(f'Alternative configuratie file {config_file} geladen.')
        self.config_options = config_options
    def get_database_name(self):
        if self.config_options.database_file:
            database = self.config_options.database_file
            config.set('configuration', 'database', database) 
        else:
            database = config.get('configuration','database') 
        return from_main_path(path_with_suffix(database, '.db'))
    def __initialize_database(self, recreate: bool)->bool:
        try:
            database = self.get_database_name()
            if not file_exists(str(database)):
                err_msg = f'Database {database} bestaat niet.'            
                if recreate:
                    log_warning(err_msg)
                else:    
                    self.validation_error = err_msg
                    log_error(err_msg)
                    return False
            self.database = initialize_database(database, recreate)
            self.storage  = initialize_storage(self.database)
            if not self.database or not self.database.connection:
                self.validation_error = f'Database {database} gecorrumpeerd of ander probleem met database'
                return False
        except Exception as Mystery:
            print(f'Error initializing database: {Mystery}')
            return False
        return True
    def __prepare_storage_roots(self, preview: bool):
        # initialize file roots BEFORE processing to cover for cases where aanvraagformulieren 
        # (stored in the output_directory) are created with the wrong root
        # this will cause problems later on
        if not preview:
            self.storage.add_file_root(str(self.root))
        if created_directory(self.output_directory):
            log_print(f'Map {self.output_directory} aangemaakt.')
        self.storage.add_file_root(str(self.output_directory))
    def __initialize_directories(self, preview: bool)->bool:        
        self.root = self.__get_directory(self.config_options.root_directory, 'root','Root directory voor aanvragen', True)
        valid = True
        if not self.root or not test_directory_exists(self.root):
            valid = False
            err_msg = f'Root directory "{self.root}" voor aanvragen niet ingesteld of bestaat niet.'
            log_error(err_msg)
        self.output_directory = self.__get_directory(self.config_options.output_directory, 'output', 'Directory voor nieuwe beoordelingsformulieren')
        if not self.output_directory:
            valid = False
            err_msg = f'Output directory "{self.output_directory}" voor aanvragen niet ingesteld.'
            log_error(err_msg)
        elif not test_directory_exists(self.output_directory):
            log_warning(f'Output directory "{self.output_directory}" voor aanvragen bestaat niet. Wordt aangemaakt.')
        if valid:
            self.__prepare_storage_roots(preview)
            return True
        else:
            self.validation_error = f'Directories voor aanvragen en/of nieuwe beoordelingsformulieren niet ingesteld.'
            return False
    def __get_directory(self, option_value, config_name, title, mustexist=False):
        def windows_style(path: str)->str:
            #because askdirectory returns a Posix-style path which causes trouble
            if path:
                return path.replace('/', '\\')
            return ''
        config_value = config.get('configuration', config_name)
        if (option_value is not None and not option_value) or (config_value == ""):
            result = windows_style(tkifd.askdirectory(mustexist=mustexist, title=title))
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
    def __must_recreate(self, processing_options: AAPAProcessingOptions)->bool:
        result= (AAPAaction.NEW in processing_options.actions) and\
               (not file_exists(self.get_database_name()) or processing_options.force or verifyRecreate())        
        return result
    def __initialize_database_part(self, processing_options: AAPAProcessingOptions)->bool:
        return self.__initialize_database(self.__must_recreate(processing_options))
    def __initialize_directories_part(self, processing_options: AAPAProcessingOptions)->bool:
        return self.__initialize_directories(preview=processing_options.preview)
    def initialize(self, processing_options: AAPAProcessingOptions, part = PART.BOTH)->bool:
        match part:
            case AAPAConfiguration.PART.DATABASE:
                return self.__initialize_database_part(processing_options)
            case AAPAConfiguration.PART.DIRECTORIES:
                return self.__initialize_directories_part(processing_options)
            case AAPAConfiguration.PART.BOTH:
                db_valid = self.__initialize_database_part(processing_options) 
                dir_valid = self.__initialize_directories_part(processing_options)
                return db_valid and dir_valid
        # if self.options.history_file is not None:
        #     self.options.history_file = path_with_suffix(self.__get_history_file(self.options.history_file), '.xlsx')
