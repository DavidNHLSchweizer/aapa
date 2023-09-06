from dataclasses import dataclass
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Protocol
from general.fileutil import created_directory, from_main_path, path_with_suffix, test_directory_exists
from general.singleton import Singleton

class PrintFunc(Protocol):
    def __call__(msg: str):pass

@dataclass
class PrintFuncs:
    print:PrintFunc=print
    info:PrintFunc=print
    warning:PrintFunc=print
    error:PrintFunc=print
    
class ConsoleFactory:
    def create(self)->PrintFuncs:
        return None
    
class ConsolePrinter(Singleton):
    def __init__(self):
        self._funcs:PrintFuncs = None
        self._previous:list[PrintFuncs] = []
    def push_console(self, funcs:PrintFuncs):
        self._previous.append(self._funcs)
        self._funcs = funcs
    def pop_console(self)->PrintFuncs:
        if self._previous == []:
            return None
        self._funcs = self._previous.pop()
        return self._funcs
    def __check_func(self, func_name: str, msg: str):
        if self._funcs:
            func = getattr(self._funcs, func_name, None)
            if func:
                func(msg)
            else:
                print(msg)
        else:
            print(msg)
    def print(self, msg: str):
        self.__check_func('print', msg)
    def info(self, msg: str):
        self.__check_func('info', msg)
    def warning(self, msg: str):
        self.__check_func('warning', msg)
    def error(self, msg: str):
        self.__check_func('error', msg)

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

def console_info(msg: str):
    if _console:
        _console.info(msg)
    else:
        print(msg)

def log_info(msg: str, to_console=False):
    if _logger:
        _logger.info(msg)
    if to_console:
        console_info(msg)

def console_print(msg: str):
    if _console:
        _console.print(msg)
    else:
        print(msg)

def log_print(msg: str):
    if _logger:
        _logger.info(msg)
    console_print(msg)

def console_warning(msg: str):
    if _console:
        _console.warning(msg)
    else:
        print(f'WARNING: {msg}')

def log_warning(msg: str, to_console=True):
    if _logger:
        _logger.warning(msg)
    if to_console:
        console_warning(msg)

def console_error(msg: str):    
    if _console:
        _console.error(msg)
    else:
        print(f'ERROR: {msg}')

def log_error(msg: str):
    if _logger:
        _logger.error(msg)
    console_error(msg)

class DefaultConsoleFactory(ConsoleFactory):
    def create(self)->PrintFuncs:
        return PrintFuncs(console_print, console_info, console_warning, console_error)
    
#functions to switch printing to other channels, e.g. a terminal widget
def push_console(funcs: PrintFuncs):
    if _console:
        _console.push_console(funcs)

def pop_console()->PrintFuncs:
    if _console:
        return _console.pop_console()
    return None

push_console(DefaultConsoleFactory().create())