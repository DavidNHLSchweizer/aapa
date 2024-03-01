from main.log import log_exception

class ObsoleteException(Exception): pass

def obsolete_exception(msg: str):
    log_exception(ObsoleteException(f'call to obsolete function: {msg}'))