from general.config import ListValueConvertor, config
from general.fileutil import file_exists

def init_config():
    config.register('debug', 'disabled_loggers', ListValueConvertor)
    config.register('debug', 'enabled_loggers', ListValueConvertor)
init_config()

def load_debug_config():
    DISABLED = "[DISABLED]"
    ENABLED = "[ENABLED]"
    if not (filename := config.get('debug', 'debug_config')) or not file_exists(filename):
        return
    disabled = False
    enabled =  False
    disabled_loggers = []
    enabled_loggers = []
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
                if not l in disabled_loggers:
                    disabled_loggers.append(l)
            elif enabled:
                if not l in enabled_loggers:
                    enabled_loggers.append(l)
    config.set('debug', 'disabled_loggers', disabled_loggers)
    config.set('debug', 'enabled_loggers', enabled_loggers)
