import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from general.fileutil import created_directory, from_main_path, path_with_suffix, test_directory_exists, get_main_module_path
from general.singleton import Singleton

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

_logger = None

def init_logging(filename: str):
    global _logger 
    _logger = AAPAlogger(filename)

def logInfo(msg: str):
    if _logger:
        _logger.info(msg)

def logPrint(msg: str):
    if _logger:
        _logger.info(msg)
    print(msg)

def logWarning(msg: str, to_console=True):
    if _logger:
        _logger.warning(msg)
    if to_console:
        print(f'WARNING: {msg}')

def logError(msg: str):
    if _logger:
        _logger.error(msg)
    print(f'ERROR: {msg}')
