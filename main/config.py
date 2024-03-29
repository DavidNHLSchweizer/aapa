from __future__ import annotations
import atexit
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path
from general.fileutil import file_exists, from_main_path, get_main_module_path
from general.singleton import Singleton

class ValueConvertor:
    def __init__(self, parser: ConfigParser):
        self._parser = parser
    def get(self, section_key: str, key_value: str, **kwargs)->str:
        if (section := self._parser[section_key]) is not None:
            return section.get(key_value, **kwargs)
        return None
    def set(self, section_key: str, key_value: str, value: object):
        if (section := self._parser[section_key]) is not None:
            section[key_value] = str(value)

class IntValueConvertor(ValueConvertor):
    def get(self, section_key: str, key_value: str, **kwargs)->int:
        try:
            return self._parser.getint(section_key, key_value, **kwargs)
        except (NoSectionError, NoOptionError):
            return None
class FloatValueConvertor(ValueConvertor):
    def get(self, section_key: str, key_value: str, **kwargs)->float:
        try:
            return self._parser.getfloat(section_key, key_value, **kwargs)
        except (NoSectionError, NoOptionError):
            return None
class BoolValueConvertor(ValueConvertor):
    def get(self, section_key: str, key_value: str, **kwargs)->bool:
        try:
            return self._parser.getboolean(section_key, key_value, **kwargs)
        except (NoSectionError, NoOptionError):
            return None

class ListValueConvertor(ValueConvertor):
    def __init__(self, parser: ConfigParser, item_convertor: type[ValueConvertor] = None):
        super().__init__(parser)
        self.item_convertor = item_convertor(parser) if item_convertor else None
    def __next_item(self, section_key, item_key, **kwargs):
        try:
            if self.item_convertor:
                return self.item_convertor.get(section_key, item_key, **kwargs)
            else:
                return super(ListValueConvertor, self).get(section_key, item_key, **kwargs)
        except (NoSectionError, NoOptionError):
            return None 
    def get(self, section_key: str, key_value: str, **kwargs)->str:
        result = []
        nn = 0
        while (item := self.__next_item(section_key, ListValueConvertor.item_key(key_value, nn), **kwargs)) is not None:
            result.append(item)
            nn+=1
        return result
    def set(self, section_key: str, key_value: str, value: object):
        n_previous_items = len(self.get(section_key, key_value))
        for n1, item in enumerate(value):
            item_key = ListValueConvertor.item_key(key_value, n1)
            if self.item_convertor:
                self.item_convertor.set(section_key, item_key, item)
            else:
                super().set(section_key, item_key, str(item))
        for n1 in range(len(value), n_previous_items):
            self._parser.remove_option(section_key, ListValueConvertor.item_key(key_value, n1))            
    @staticmethod
    def item_key(key_value, n1):
        return f'{key_value}_{n1+1}'
    
class ValueConvertors:
    def __init__(self, parser: ConfigParser):
        self._register = []
        self._parser = parser
    def register(self, section_key: str, key_value: str, convertor_class: type[ValueConvertor], **kwargs):
        if (entry := self._register_entry(section_key, key_value)) is not None:
            self._register.remove(entry)
        self._register.append({'section': section_key, 'key': key_value, 'convertor': convertor_class(self._parser, **kwargs)})
    def _register_entry(self, section_key: str, key_value: str):
        for entry in self._register:
            if entry['section']==section_key and entry['key']==key_value:
                return entry
        return None
    def _get_convertor(self, section_key: str, key_value: str)->ValueConvertor:
        if (entry := self._register_entry(section_key, key_value)) is not None:
            return entry['convertor']
        return None
    def get(self, section_key: str, key_value: str, **kwargs):
        try:
            if (convertor :=  self._get_convertor(section_key, key_value)) is not None:
                return convertor.get(section_key, key_value, **kwargs)
            else:
                return self._parser[section_key][key_value]
        except KeyError as E:
            return None
    def set(self, section_key: str, key_value: str, value):
        if (convertor :=  self._get_convertor(section_key, key_value)) is not None:
            convertor.set(section_key, key_value, value)
        else:
            self._parser[section_key][key_value] = value

def config_as_string(conf: Config)->str:
    result = ''
    for section_key in conf.sections:
        result = result + f'[{section_key}]\n'
        for key, value in conf.items(section_key):
            result = result + f'\t{key} = {value}\n'
    return result

class Config(Singleton):
    def __init__(self):
        self._parser = ConfigParser()
        self._convertors = ValueConvertors(self._parser)
    def __str__(self):
        return config_as_string(self)
    @property
    def sections(self):
        return self._parser.sections()
    def section(self, section_key):
        return self._parser[section_key]
    def items(self, section_key):
        return self.section(section_key).items()
    def get(self, section_key: str, key_value: str):
        return self._convertors.get(section_key, key_value)
    def register(self, section_key: str, key_value: str, convertor_class: type[ValueConvertor], **kwargs):
        if convertor_class:
            self._convertors.register(section_key, key_value, convertor_class, **kwargs)
    def init(self, section_key: str, key_value: str, value):
        if not self.get(section_key, key_value):
            self.set(section_key, key_value, value)
    def set(self, section_key: str, key_value: str, value):
        if not section_key in self._parser.sections():
            self._parser.add_section(section_key)
        self._convertors.set(section_key, key_value, value)
    def write(self, filename: str):
        with open(filename, "w", encoding='utf-8') as file:
            self._parser.write(file)
    def clear(self):
        self._parser.clear()
    def read(self, filename: str):
        self._parser.read(filename)

AAPA_CODE= ':AAPA:'
def decode_aapa_path(filename: str|Path)->str:
    return str(filename).replace(AAPA_CODE, str(get_main_module_path()))
    
CONFIG_FILE_NAME = 'aapa_config.ini'
config = Config()

def init_config():
    config.init('templates', 'directory', r':AAPA:\templates')
init_config()

def get_templates(filename: str=None)->Path:
    if filename:
        return Path(decode_aapa_path(config.get('templates', 'directory'))).joinpath(filename)
    else:
        return Path(decode_aapa_path(config.get('templates', 'directory')))
    
def _get_config_file():
    try:
        return from_main_path(CONFIG_FILE_NAME)
    except:
        return None

def _load_config():
    global config
    try:
        config_file = _get_config_file()
        if config_file and file_exists(config_file):
            config.read(config_file)
    except Exception as E:
        print(f'Fout bij lezen configuratiebestand {config_file}: {E}')
_load_config()

@atexit.register
def _save_config():    
    config_file = _get_config_file()
    if config_file:
        config.write(config_file)
