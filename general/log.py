from dataclasses import dataclass
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Protocol
from general.fileutil import created_directory, from_main_path, path_with_suffix, test_directory_exists, get_main_module_path
from general.singleton import Singleton

class printFunc(Protocol):
    def __call__(msg: str):pass

@dataclass
class printFuncs:
    print:printFunc=print
    warning:printFunc=print
    error:printFunc=print
    
class ConsolePrinter(Singleton):
    def __init__(self):
        self._funcs:printFuncs = None
        self._previous:list[printFuncs] = []
    def push_console(self, funcs:printFuncs):
        self._previous.append(self._funcs)
        self._funcs = funcs
    def pop_console(self)->printFuncs:
        if self._previous == []:
            return None
        self._funcs = self._previous.pop()
        return self._funcs
    def print(self, msg: str):
        if self._funcs and self._funcs.print:
            self._funcs.print(msg)
        else:
            print(msg)
    def warning(self, msg: str):
        if self._funcs and self._funcs.warning:
            self._funcs.warning(msg)
        else:
            print(msg)
    def error(self, msg: str):
        if self._funcs and self._funcs.error:
            self._funcs.error(msg)
        else:
            print(msg)

class AAPAlogger(Singleton):
    def __init__(self, filename):        
        logpath = from_main_path('logs')
        if not (test_directory_exists(logpath) or created_directory(logpath)):
            print(f'ERROR: can not create logfile {filename} in {logpath}')            
            logpath = Path('.').resolve()
            print(f'Creating log in {logpath}')        
        filename = path_with_suffix(logpath.joinpath(Path(filename).name), '.log')
        logging.basicConfig(handlers=[TimedRotatingFileHandler(str(filename),'D', 1, 7, encoding='utf-8')], format='%(asctime)s- %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    def info(self, msg):
        logging.info(msg)
    def warning(self, msg):
        logging.warning(msg)
    def error(self, msg):
        logging.error(msg)

_logger: AAPAlogger = None
_console: ConsolePrinter = None

def init_logging(filename: str):
    global _logger, _console
    _logger = AAPAlogger(filename)
    _console = ConsolePrinter()

def logInfo(msg: str):
    if _logger:
        _logger.info(msg)

def logPrint(msg: str):
    if _logger:
        _logger.info(msg)
    if _console:
        _console.print(msg)
    else:
        print(msg)

def logWarning(msg: str, to_console=True):
    if _logger:
        _logger.warning(msg)
    if to_console:
        if _console:
            _console.warning(msg)
        else:
            print(f'WARNING: {msg}')

def logError(msg: str):
    if _logger:
        _logger.error(msg)
    if _console:
        _console.error(msg)
    else:
        print(f'ERROR: {msg}')

#functions to switch printing to other channels, e.g. a terminal widget
def push_console(funcs: printFuncs):
    if _console:
        _console.push_console(funcs)

def pop_console()->printFuncs:
    if _console:
        return _console.pop_console()
    return None