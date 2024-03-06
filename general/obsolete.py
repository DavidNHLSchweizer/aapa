from main.log import log_exception

class ObsoleteException(Exception): pass

def obsolete_exception(msg: str):
    log_exception(f'call to obsolete function: {msg}', ObsoleteException)