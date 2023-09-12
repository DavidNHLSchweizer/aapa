from general.config import ListValueConvertor, config
from general.fileutil import file_exists

def init_config():
    config.register('debug', 'disabled_loggers', ListValueConvertor)
init_config()

def load_debug_config():
    if not (filename := config.get('debug', 'debug_config')) or not file_exists(filename):
        print(f'sexy {filename}')
        return
    disabled_loggers = []
    with open(filename, mode='r') as file:
        for l in file.readlines():
            if l and l[0] == '#':

                continue
            l = l.strip()
            if l and not l in disabled_loggers:
                disabled_loggers.append(l)
    config.set('debug', 'disabled_loggers', disabled_loggers)
