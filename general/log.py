import logging

def logInfo(msg: str):
    logging.info(msg)

def logPrint(msg: str):
    logInfo(msg)

def logWarning(msg: str):
    logging.warning(msg)
    print(f'WARNING: {msg}')

def logError(msg: str):
    logging.error(msg)
    print(f'ERROR: {msg}')
