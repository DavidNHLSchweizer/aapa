import sys
from general.fileutil import file_exists
from general.singleton import Singleton
import jsonpickle
import atexit
from pathlib import Path

class ConfigSection:
    def __init__(self, section_key):
        self.section_key = section_key
        self._entries = {}
    def __str__(self):
        return f'{self.section_key}:\n\t' + ','.join([f'{key}:{value}' for key, value in self._entries.items()])
    def __len__(self):
        return len(self._entries)
    def set_default(self, value_key: str, default_value):
        if not self._entries.get(value_key, None):          
            self._entries[value_key] = default_value            
    def set(self, value_key: str, value):
        self._entries[value_key] = value
    def get(self, value_key, default):
        return self._entries.get(value_key, default)
    def remove_key(self,value_key):
        self._entries.pop(value_key, None)
    def __ini_write_key(self, key, value, ini):
        ini.write(f'{key}={value}\n')
    def ini_write(self, ini):
        ini.write(f'[{self.section_key}]\n')
        for key,value in self._entries.items():
            self.__ini_write_key(key, value, ini)
    def entries(self)->tuple[str,any]:
        return self._entries.items()

class Config (Singleton):
    def __init__(self):
        self._reset()    
    def get(self, section_key: str, value_key: str):
        return self.__get_section(section_key).get(value_key, None)
    def set_default(self, section_key: str, value_key: str, default_value):
        self.__get_section(section_key).set_default(value_key, default_value)        
    def set(self, section_key: str, value_key: str, value):
        self.__get_section(section_key).set(value_key, value)    
    def remove_key(self, section_key, value_key):
        if section := self.__get_section(section_key):
            section.remove_key(value_key)
    def ini_write(self, filename): 
        #TODO not very useful because several items are not supported
        #should do through configparser anyway
        with open(filename, mode='w') as ini:
            for section_key in self.__sections.keys():
                self.__get_section(section_key).ini_write(ini)
            
    def write(self, fp): #TODO: do this  (and read, obviously) in a more readable fileformat, e.g. .INI 
                        # (challenge: make it work for lists, enum or dicts, 
                        # without knowing anything about the underlying data)
                        #TODO ISSUES: a) raw string support
                        #             b) list[string] support
                        #             c) list [dict] support (see options.mode_patterns) (which can probably also be refactored)
        fp.write(jsonpickle.encode(self))
    def read(self, fp):
        return jsonpickle.decode(fp.read())
    def _reset(self): 
        self.__sections = {}
    def __add_section(self, section_key: str):
        self.__sections[section_key] = ConfigSection(section_key)
        return self.__sections[section_key]
    def __get_section(self, section_key: str)->ConfigSection:
        if result := self.__sections.get(section_key, None):
            return result
        return self.__add_section(section_key)
    def __str__(self):
        return '\n'.join([str(self.__get_section(key)) for key in self.__sections.keys()])

application_root = Path(sys.argv[0]).resolve().parent
CONFIG_FILE_NAME = 'aapa_config.json'
config = Config()

def _get_config_file():
    try:
        return Path(application_root).joinpath(CONFIG_FILE_NAME)
    except:
        return None

def _load_config():
    global config
    try:
        config_file = _get_config_file()
        if config_file and file_exists(config_file):
            with open(config_file, 'r') as file:
                config = config.read(file)
    except Exception as E:
        print(f'Fout bij lezen configuratiebestand {config_file}: {E}')
_load_config()

@atexit.register
def _save_config():    
    config_file = _get_config_file()
    if config_file:
        with open(config_file, 'w', encoding='utf-8') as file:
            config.write(file)
