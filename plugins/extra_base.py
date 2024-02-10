from argparse import ArgumentParser, Namespace
from asyncio import Protocol
import importlib
from pathlib import Path
import re
from types import ModuleType

from data.storage.aapa_storage import AAPAStorage
from general.log import log_info, log_print
from general.sql_coll import SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext

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

# TODO: werk dit om naar deze vorm, is niet strikt noodzakelijk.
# class ExtraModule:
#     def __init__(self, module_name: str):
#         self.module_name = module_name
#         self.module = self._find_module(module_name)
#         self.module_main = self._find_module_main(self.module, module_name)
#         if not (self.module and self.module_main):
#             print('...stopped.')  
#             return None        
#     def _find_module(self, module_name: str)->ModuleType:
#         full_module_name = f'extra.{module_name}'
#         try:
#             module = importlib.import_module(full_module_name)
#             return module
#         except ModuleNotFoundError as E:
#             print(E)
#             return None
#     def _find_module_main(self, module: ModuleType, module_name: str)->OneTimeFunc:
#         if not (main := getattr(module, 'extra_main', None)):
#             print(f'Entry class "extra_main" not found in {module_name}.')
#             return None
#         elif not isinstance(main,ExtraModule):
#             print(f'"extra_main" class {main.__class__} in {module_name} is not a valid ExtraModule class.')
#             return None
#         return main
#     def _init_parser(self)->Namespace:
#         simple_parser = ArgumentParser(description='Script om (in principe) eenmalige acties uit te voeren voor AAPA.', prog='onetime', 
#                                         usage='%(prog)s module [opties].\n\tOpties zijn, naast alle opties die voor de module zijn gedefinieerd,\n\talle opties die in AAPA mogelijk zijn.')
#         simple_parser.add_argument('module', type=str, 
#                             help='Naam module om uit voeren (wordt verwacht in directory "extra", entry point: extra_main (ExtraModule subclass))')
#         simple_parser.add_argument('-module_help', action="store_true", help='Hulp voor de uit te voeren module')
#         simple_args,_ = simple_parser.parse_known_args()
#         return simple_args
    
#     def run(self):
#         simple_args = self._init_parser()
#         module_name = simple_args.module
#         if (module := self._find_module(module_name)) is None or (module_main := self._find_module_main(module, module_name)) is None:
#             print('...stopped.')  
#             exit()
        
#         if (extra_args:=self.find_extra_args(module)):
#             parser = extra_args(simple_parser)
#         else:
#             parser = simple_parser
#         if simple_args.module_help: 
#             print(module.__doc__)
#             print('-------------------------------')
#             parser.print_help()
#             exit()
#         args,other_args = aapa_parser(parser, include_actions=False).parse_known_args()   
#         (config_options, processing_options) = _get_options_from_commandline(args)
#         init_logging(f'{module_name}.log', processing_options.debug)
#         with AAPARunnerContext(AAPAConfiguration(config_options), processing_options,
#                             message=f'--- Running {module_name} ---'
#                             ) as context:
#             if context:
#                 extra_main(context, namespace= args)
#                 ready=True
#             else:
#                 ready=False
#                 print('...stopped.')
#         if ready:
#             log_info('...ready')
