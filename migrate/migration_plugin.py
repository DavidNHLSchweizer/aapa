from abc import abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from types import ModuleType
from main.log import log_info, log_print
from general.sql_coll import SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext

class MigrationPlugin(PluginBase):
    def __init__(self, module: ModuleType):
        super().__init__(module)
        self.module_path = Path(self.module.__name__.replace('.','\\')).parent
    def log(self, msg: str):
        if self.verbose:
            log_print(msg)
        else:
            log_info(msg)
    def get_json_filename(self, module_file: str)->str:
        base = Path(module_file).stem
        return f'{base}.json'
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('-json', action='store_true',help='if True: create SQL output for later execution.') 
        parser.add_argument('--json_directory', type=str,dest='json_directory', help='Alternate directory for json output. If not set, the .JSON file will be in the same directory as the plugin module') 
        parser.add_argument('-v', '--verbose', action="store_true", help='If true: logging gaat naar de console ipv het logbestand.')
        return parser
    def init_SQLcollectors(self)->SQLcollectors:
        return SQLcollectors()
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        log_print('------------------')
        log_print('--- processing ---')
        log_print('------------------')
        self.storage = context.configuration.storage
        self.verbose=kwdargs.get('verbose', False)
        self.json = kwdargs.get('json', False)
        self.json_path = kwdargs.get('json_directory', None)
        if not self.json_path:
            self.json_path = self.module_path
        self.sql=self.init_SQLcollectors()
        return True
    def after_process(self, context: AAPARunnerContext, process_result: bool):        
        if self.json:
            filename = self.json_path.joinpath(self.get_json_filename(self.module_name))
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')      
