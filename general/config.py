from general.fileutil import test_file_exists
from general.singleton import Singleton
import jsonpickle
import atexit
from pathlib import Path

class Config (Singleton):
    def __init__(self):
        self._reset()
    def get(self, section_key: str, value_key: str):
        if section:=self.__get_section(section_key):
            return section.get(value_key, None)
        return None
    def set_default(self, section_key: str, value_key: str, default_value):
        if not (section:=self.__get_section(section_key)):
            self.__sections[section_key] = {value_key: default_value}
        else:
            if not section.get(value_key, None):          
                section[value_key] = default_value            
    def set(self, section_key: str, value_key: str, value):
        if not (section:=self.__get_section(section_key)):
            self.__sections[section_key] = {value_key: value}
        else:
            section[value_key] = value

    def ini_write(self, filename):
        with open(filename, mode='w') as ini:
            for key in self.__sections.keys():
                ini.write(f'[{key}]')
            
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
    def __get_section(self, section_key: str)->dict:
        return self.__sections.get(section_key, None)
    def __section_str(self, section_key: str)->str:
        if section:=self.__get_section(section_key):
            return f'{section_key}:\n\t' + ','.join([f'{key}:{value}' for key, value in section.items()])
        else:
            return None
    def __str__(self):
        return '\n'.join([self.__section_str(key) for key in self.__sections.keys()])

config = Config()

def _get_config_file():
    try:
        return Path(config.get('general', 'default_directory')).joinpath(config.get('general', 'config_file'))
    except:
        return None

def _load_config():
    config_file = _get_config_file()
    if config_file and test_file_exists(config_file):
        with open(config_file, 'r') as file:
            config = config.read(file)
_load_config()

@atexit.register
def _save_config():    
    config_file = _get_config_file()
    if config_file:
        with open(config_file, 'w', encoding='utf-8') as file:
            config.write(file)
