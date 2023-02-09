import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from general.fileutil import path_with_suffix
from general.singleton import Singleton

class AAPAlogger(Singleton):
    def __init__(self, filename):  
        filename = path_with_suffix(Path(filename).parent.joinpath('logs').joinpath(Path(filename).name), '.log') 
        logging.basicConfig(handlers=[TimedRotatingFileHandler(filename,'D', 1, 7, encoding='utf-8')], format='%(asctime)s- %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
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

def logWarning(msg: str):
    if _logger:
        _logger.warning(msg)
    print(f'WARNING: {msg}')

def logError(msg: str):
    if _logger:
        _logger.error(msg)
    print(f'ERROR: {msg}')
