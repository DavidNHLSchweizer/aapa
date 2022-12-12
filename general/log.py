import logging

def logPrint(msg: str):
    logging.info(msg)
    print(msg)

def logWarn(msg: str):
    logging.warn(msg)
    print(f'WARNING: {msg}')

def logError(msg: str):
    logging.error(msg)
    print(f'ERROR: {msg}')
