from argparse import ArgumentParser
from pathlib import Path
import re
from general.log import log_info, log_print
from general.sql_coll import SQLcollectors
from plugins.plugin import PluginBase
from process.aapa_processor.aapa_processor import AAPARunnerContext

class MigrationPlugin(PluginBase):
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
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 
        parser.add_argument('-v', '--verbose', action="store_true", help='If true: logging gaat naar de console ipv het logbestand.')
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        log_print('------------------')
        log_print('--- processing ---')
        log_print('------------------')
        self.storage = context.configuration.storage
        self.verbose=kwdargs.get('verbose', False)
        self.sql=SQLcollectors()
        return True
    def after_process(self, context: AAPARunnerContext, **kwdargs):        
        if migrate_dir := kwdargs.get('migrate_dir', None):            
            filename = Path(migrate_dir).resolve().joinpath(self.get_json_filename(self.module_name))
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')      
