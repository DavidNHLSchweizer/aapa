import logging
import pkgutil
from general.classutil import find_calling_module
from general.fileutil import file_exists, from_main_path
from general.singleton import Singleton

MAJOR_DEBUG_DIVIDER = "-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*"
MINOR_DEBUG_DIVIDER = "--------------------------------------------------------"
ITEM_DEBUG_DIVIDER =  "........................................................"
class _ModuleData:
    def __init__(self, module_name: str, enabled: bool = True):
        if (root_loc := module_name.find('*')) != -1:
            self.module_name = module_name[:root_loc-1 ]
        else:
            self.module_name = module_name
        self.enabled = enabled
    def is_enabled(self, module_name: str)->bool:
        if not self.enabled:
            return False
        return module_name[:len(module_name)] == self.module_name
    
class _ModuleInfo(list[_ModuleData]):
    def add(self, module_name: str, enabled: bool=True):
        self.append(_ModuleData(module_name, enabled=enabled))
        self.sort(key=lambda m: (m.module_name, len(m.module_name)), reverse=True)
    def _find(self, module_name:str)->_ModuleData:
        for data in self:
            if module_name == data.module_name or module_name.find(data.module_name) == 0:
                return data
        return None
    def is_enabled(self, module_name: str)->bool:
        if (data:=self._find(module_name)):
            return data.enabled
        return False


class DebugConfig(Singleton):
    def __init__(self):
        self.info = _ModuleInfo()
        self.info.add('__main__')
    def enabled_loggers(self)->list[str]:
        return [info.module_name for info in self.info if info.enabled]
    def disabled_loggers(self)->list[str]:
        return [info.module_name for info in self.info if not info.enabled]
    def read(self, filename: str)->bool:
        DISABLED = "[DISABLED]"
        ENABLED = "[ENABLED]"
        if not file_exists(filename):
            return
        enabled =  False
        with open(filename, mode='r') as file:
            for l in file.readlines():
                l = l.strip()
                if not l:
                    continue
                if l in {DISABLED, ENABLED}:
                    enabled = l == ENABLED
                    continue
                elif l[0] == '#':
                    continue
                self.info.add(l, enabled)
    def module_is_enabled(self, module_name: str)->bool:
        return self.info.is_enabled(module_name)
    def _initialize_disabled_loggers(self):
        for module_name,logger in logging.root.manager.loggerDict.items():
            logger.disabled = not module_is_enabled(module_name)
DEBUG_CONFIG_FILE_NAME = 'debug/debug_config.'
_debug_config =  DebugConfig()

def _get_config_file():
    try:
        return from_main_path(DEBUG_CONFIG_FILE_NAME)
    except:
        return None
def _load_debug_config():
    global _debug_config
    try:
        debug_config_file = _get_config_file()
        if debug_config_file and file_exists(debug_config_file):
            _debug_config.read(debug_config_file)
    except Exception as E:
        print(f'Fout bij lezen debug-configuratiebestand {debug_config_file}: {E}')
_load_debug_config()

def module_is_enabled(module_name: str)->bool:
    return _debug_config.module_is_enabled(module_name)
def check_caller_is_enabled(calling_module: str)->bool:
    caller = find_calling_module(calling_module)
    return module_is_enabled(caller)
def get_disabled_loggers()->list[str]:
    return _debug_config.disabled_loggers()
def get_enabled_loggers()->list[str]:
    return _debug_config.enabled_loggers()
def initialize_disabled_loggers():
    _debug_config._initialize_disabled_loggers()


