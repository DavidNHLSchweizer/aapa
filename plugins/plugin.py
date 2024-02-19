""" Classes for AAPA plugins.

    Plugins are small programs that are called within the AAPA context activated.
    Through this, the program can access the storage layer and the AAPA options.

    The idea is to use this to add functionality to AAPA that is not usefu=l to 
    have in the main program. 
    
    Plugins can do things that need access to AAPA data. Examples are database 
    manipulation to correct inconsistencies, or migration scripts.

    Simple guide
    ------------

    First subclass PluginBase and implement as a minimum the abstract method process. 
    More information on this : see class PluginBase documentation,
   
    Then run using class PluginRunner. 
     More information on this : see class PluginRunner documentation,   

"""

from dataclasses import dataclass
import importlib
import inspect
from abc import ABC, abstractmethod
from argparse import ArgumentParser
import sys
from types import ModuleType
from typing import Type
from main.args import aapa_parser

from main.options import AAPAConfigOptions, AAPAProcessingOptions, _get_options_from_commandline
from main.log import init_logging, log_warning
from process.main.aapa_config import AAPAConfiguration
from process.main.aapa_processor import AAPARunnerContext

class PluginException(Exception):pass

class PluginBase(ABC):
    """ Base class for plugins 

    Public methods
    --------------

    process: the method that does actual processing
            this is an abstract method: must be implemented in every subclass.

    run: the actual processing. This will normally be called by a PluginRunner.
    get_parser: gets parser object. subclass this if your plugin needs custom arguments from the commandline.
    usage: simple help called when -h is in the command line options.
    before_process: called before process, to set up the processing environment.
    after_process: called after process.

    """
    def __init__(self, module: ModuleType):
        """
        parameters
        ----------
        module: ModuleType information as supplied by importlib.

        """
        self.module = module
        self.module_name = module.__name__.split('.')[-1]
    @staticmethod
    def _unlistify(list_arg:list[list[str]])->list[str]:
        """ Converts list arguments from argument parser to simple list of strings 
        
            action='append' produces every --list_arg=xxx argument as [xxx],
            so we get [[xxx1],[xxx2]...]. This "unlists" this to a simple list of strings.

        """
        if not list_arg:
            return []
        return [as_list[0] for as_list in list_arg]

    def get_parser(self)->ArgumentParser:
        """ initializes the command line options parser.     
             
            returns
            -------
            ArgumentParser with the option -plugin_help.
                -plugin_help triggers the usage_funtion.

            A subclass can add extra command line options by overloading get_parser. 
            It is expected (but not mandatory) that you call the superclass get_parser and add to that.

        """
        parser = ArgumentParser(prog=self.module_name, 
                                usage='%(prog)s [opties].\n\tOpties zijn, naast alle opties die voor de module zijn gedefinieerd,\n\talle opties die in AAPA mogelijk zijn.')
        parser.add_argument('-plugin_help', action="store_true", help='Hulp voor deze module')
        return parser
    def usage(self,parser: ArgumentParser):
        """ prints usage information """
        if self.module.__doc__:
            print(self.module.__doc__)
        parser.print_help()
    def _get_options(self, args: list[str]= None)->tuple[AAPAConfigOptions, AAPAProcessingOptions]:
        if not args:
            args = sys.argv
        parser = self.get_parser()
        module_args,other_args = parser.parse_known_args(args)
        self.module_options = module_args.__dict__
        plugin_help = self.module_options.pop('plugin_help',False)
        if plugin_help:
            self.usage(parser)
            return (None,None)
        aapa_args,unknown_args = aapa_parser(parser, include_actions=False).parse_known_args(other_args)
        if unknown_args:
            log_warning(f'Onbekende optie(s) ingevoerd: {unknown_args}.')
        self.aapa_dict = aapa_args.__dict__
        return _get_options_from_commandline(aapa_args)
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        """ Called before the process method 
        
        Overload this to set up the processing environment, e.g. necessary variables.
        This method should only be called from PluginBase.run (which is called from PluginRunner.run()).

        parameters
        ----------
        context: the AAPA context manager that can be used to access the AAPA variables.
            See AAPARunnerContext for more info,
        **kwdargs: dictionary object with the values of the module-specific arguments.  
            these are supplied in get_parser.            

        returns
        -------
        Default is True. If for some reason you want to halt processing, return False. 
        In that case, the process method is not called.

        """
        return True
    @abstractmethod
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        """ the actual processing of the plugin.

        This MUST be overloaded in any subclass implementing PluginBase. 
        This method should only be called from PluginBase.run (which is called from PluginRunner.run()).
        
        parameters
        ----------
        context: the AAPA context manager that can be used to access the AAPA variables.
            See AAPARunnerContext for more info,
        **kwdargs: dictionary object with the values of the module-specific arguments.  
            these are supplied in get_parser.            

        returns: expected to be True if processing is succesful, False otherwise.
        
        """
        pass
        #this MUST be implemented in a subclass
    def after_process(self, context: AAPARunnerContext, process_result: bool):
        """ Called after the process method 
        
        Overload this to perform post-processing.
        This method should only be called from PluginBase.run (which is called from PluginRunner.run()).

        parameters
        ----------
        context: the AAPA context manager that can be used to access the AAPA variables.
            See AAPARunnerContext for more info,
        process_result: the result returned by the process method.             

        """
        pass
    def run(self, args: list[str]=None)->bool:
        """ Entry point for the PluginRunner. The actual processing of the plugin.
        
        Reads command line options, sets up AAPA environment context and then calls the 
        process methods before_process, process and after_process.

        The run method should only be called from PluginBase.run (which is called from PluginRunner.run()).
        
        There is probably no reason to overload run, any customization can be done in before_process, 
        process and after_process

        parameters
        ----------
        args: The command line options supplied to the program. If args is None, the command line arguments are used.

        returns
        -------
        False if some error occurred.

        """
        config_options, processing_options = self._get_options(args)
        if not config_options or not processing_options:
            return False
        init_logging(f'{self.module_name}.log', processing_options.debug)
        with AAPARunnerContext(AAPAConfiguration(config_options), processing_options) as context:
            result = False
            if not context:
                print('...Stopping')
                return False
            if self.before_process(context, **self.module_options):
                result = self.process(context, **self.module_options)
                self.after_process(context, result)
            else:
                print('before_process returned False. Stopping...')
        return result

@dataclass
class PluginInfo:
    module: ModuleType
    module_name: str
    plugin_name: str
    plugin_class: type[PluginBase]

class PluginRunner:
    """ PluginRunner
    
        class to run Plugins (based on PluginBase).

        parameters
        ----------
        module: the plugin module or modules to run.
                you can either submit one module as a single string,
                or multiple modules as a list of strings.

        methods
        -------
        run: run the plugin or plugins.
        
    """
    def __init__(self, module: str|list[str]):
        self.modules:list[PluginInfo] = []
        if isinstance(module,str):
            self._add_module(self._initialize_module(module))
        else:
            for mod_name in module:
                self._add_module(self._initialize_module(mod_name))
    def _add_module(self, info: PluginInfo):
        self.modules.append(info)
    def _initialize_module(self, module_name: str)->PluginInfo:
        if not (module := self._find_module(module_name)):
            raise PluginException(f'Module {module_name} not found.')
        plugin_name,plugin_class = self._find_plugin(module)
        if not plugin_class:
            raise PluginException(f'PluginBase-derived class not found in {module}.')
        return PluginInfo(module=module, module_name=module_name,plugin_name=plugin_name,plugin_class=plugin_class)
    def _search_bottom_class(self, plugin_classes: dict):
        #find the class that is not a subclass of another class
        bottom_class = None
        for class_type in plugin_classes.keys():
            if not bottom_class or issubclass(class_type, bottom_class):
                bottom_class = class_type
        return (plugin_classes[bottom_class], bottom_class)
    def _find_plugin(self, module: ModuleType)->tuple[str,Type[PluginBase]]:
        class_list = inspect.getmembers(module,inspect.isclass) 
        plugin_classes = {}
        for class_name, class_type in class_list:
            if class_type == PluginBase:
                continue
            elif issubclass(class_type,PluginBase):
                plugin_classes[class_type] = class_name
        if not plugin_classes:
            return None,None
        else:
            return self._search_bottom_class(plugin_classes)        
    def _find_module(self,module_name: str)->ModuleType:
        full_module_name = f'{module_name}'
        try:
            module = importlib.import_module(full_module_name)
            return module
        except ModuleNotFoundError as E:
            print(E)
            return None
    def run(self, args: list[str]=None):
        """ Run the modules
        
            parameters
            ----------
            args: either a list of strings or None
                The arguments are supplied to the Plugins 
                as commandline parameters.
                If args = None, the arguments are taken from the 
                command line parameters.

        """
        RUNNING = 'Running module '
        for info in self.modules:
            try:
                print(f'{RUNNING}{info.module_name}')
                print(f'{"-"*len(RUNNING+info.module_name)}')
                info.plugin_class(info.module).run(args=args)    
            except PluginException as E:
                print(f'Error running plugin {info.module_name}: {E}')