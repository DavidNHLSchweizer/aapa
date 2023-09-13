import inspect
import logging
import re
from general.fileutil import file_exists, from_main_path
from general.singleton import Singleton

def _find_calling_module(calling_module: str)->str:
    def find_module_name(module_str: str)->str:
        if (m := re.match("\<module '(?P<module>.*)' from (?P<file>.*)\>", module_str)):
            return m.group("module")
        return ""
    def _caller_(stack_frame: inspect.FrameInfo)->str:
        return find_module_name(str(inspect.getmodule(stack_frame[0])))       
    stack = inspect.stack()
    level = 0
    cur_module = _caller_(stack[level])
    while level < len(stack) and cur_module != calling_module:
        cur_module = _caller_(stack[level])
        level+=1
    while level < len(stack) and cur_module == calling_module:
        cur_module = _caller_(stack[level])
        level+=1
    return cur_module

class DebugConfig(Singleton):
    def __init__(self):
        self._disabled_loggers = set()
        self._enabled_loggers = {'__main__'}
    def read(self, filename: str)->bool:
        DISABLED = "[DISABLED]"
        ENABLED = "[ENABLED]"
        if not file_exists(filename):
            return
        disabled = False
        enabled =  False
        with open(filename, mode='r') as file:
            for l in file.readlines():
                l = l.strip()
                if not l:
                    continue
                if l in {DISABLED, ENABLED}:
                    disabled = l == DISABLED
                    enabled = l == ENABLED
                    continue
                elif l and l[0] == '#':
                    continue
                if disabled:
                    self.disable_module(l)
                elif enabled:
                    self.enable_module(l)        
    def module_is_enabled(self, module_name: str)->bool:
        return module_name in self._enabled_loggers and not module_name in self._disabled_loggers
    def _set_module_enabled(self, module_name: str, value: bool):
        if value:
            self._disabled_loggers.discard(module_name)
            self._enabled_loggers.add(module_name)
        else:
            self._disabled_loggers.add(module_name)
            self._enabled_loggers.discard(module_name)
        if (logger := logging.root.manager.loggerDict.get(module_name, None)):
            logger.disabled = not value
    def enable_module(self, module_name):
        self._set_module_enabled(module_name, True)
    def disable_module(self, module_name):
        self._set_module_enabled(module_name, False)

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

def enable_module(module_name: str):
    _debug_config.enable_module(module_name)
def disable_module(module_name: str):
    _debug_config.disable_module(module_name)
def module_is_enabled(module_name: str)->bool:
    return _debug_config.module_is_enabled(module_name)
def check_caller_is_enabled(calling_module: str)->bool:
    caller = _find_calling_module(calling_module)
    return module_is_enabled(caller)
def get_disabled_loggers()->list[str]:
    return list(_debug_config._disabled_loggers)
def get_enabled_loggers()->list[str]:
    return list(_debug_config._enabled_loggers)