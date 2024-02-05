from argparse import ArgumentParser, Namespace
import importlib
from types import ModuleType
from typing import Protocol
from general.args import aapa_parser, _get_options_from_commandline
from general.log import init_logging
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.aapa_processor.aapa_processor import AAPARunnerContext

def find_module(module_name: str)->ModuleType:
    full_module_name = f'extra.{module_name}'
    try:
        module = importlib.import_module(full_module_name)
        return module
    except ModuleNotFoundError as E:
        print(E)
        return None
    
class OneTimeFunc(Protocol): 
    def __call__(self, context: AAPARunnerContext, namespace: Namespace):pass
class ParserFunc(Protocol):
    def __call__(self, base_parser: ArgumentParser)->ArgumentParser:pass

def find_extra_main(module: ModuleType, module_name: str)->OneTimeFunc:
    if not (main := getattr(module, 'extra_main', None)):
        print(f'Entry point "extra_main" not found in {module_name}.')
        return None
    return main

def find_extra_args(module: ModuleType)->ParserFunc:
    return getattr(module, 'extra_args', None)

if __name__ == "__main__":
    simple_parser = ArgumentParser(description='Script om (in principe) eenmalige acties uit te voeren voor AAPA.', prog='onetime', 
                                   usage='%(prog)s module [opties]. Opties zijn alle opties die in AAPA mogelijk zijn.')
    simple_parser.add_argument('module', type=str, 
                        help='Naam module om uit voeren (wordt verwacht in directory "onetime", entry point: onetime_action)')
    simple_parser.add_argument('-module_help', action="store_true", help='Hulp voor de uit te voeren module')
    simple_args,_ = simple_parser.parse_known_args()
    module_name = simple_args.module
    if (module := find_module(module_name)) is None or (extra_main := find_extra_main(module, module_name)) is None:
        print('...stopped.')  
        exit()
    if (extra_args:=find_extra_args(module)):
        parser = extra_args(simple_parser)
    else:
        parser = simple_parser
    if simple_args.module_help: 
        print(module.__doc__)
        print('-------------------------------')
        parser.print_help()
        exit()
    args,other_args = aapa_parser(parser, include_actions=False).parse_known_args()   
    (config_options, processing_options) = _get_options_from_commandline(args)
    init_logging(f'{module_name}.log', processing_options.debug)
    with AAPARunnerContext(AAPAConfiguration(config_options), processing_options) as context:
        if context:
            extra_main(context, namespace= args)
            ready=True
        else:
            ready=False
            print('...stopped.')
    if ready:
        print('...ready.')
        