from pathlib import Path
import re

from data.storage.aapa_storage import AAPAStorage
from general.log import log_info, log_print
from general.sql_coll import SQLcollectors

class BaseMigrationProcessor:
    def __init__(self, storage: AAPAStorage, verbose=False):
        self.storage = storage
        self.verbose=verbose
        self.sql=SQLcollectors()
    def log(self, msg: str):
        if self.verbose:
            log_print(msg)
        else:
            log_info(msg)
    def get_json_filename(self, module_file: str)->str:
        MnnnPATTERN = r"^m\d\d\d_(?P<module>.*)" 
        base = Path(module_file).stem
        if match := re.match(MnnnPATTERN, base, re.IGNORECASE):
            base = match.group('module')
        return f'{base}.json'

    def processing(self):
        #implement this in subclasses, process_all is a wrapper
        pass
    def process_all(self, module_name: str, migrate_dir = None):        
        log_print('------------------')
        log_print('--- processing ---')
        log_print('------------------')
        self.processing()
        if migrate_dir:            
            filename = Path(migrate_dir).resolve().joinpath(self.get_json_filename(module_name))
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')
       

