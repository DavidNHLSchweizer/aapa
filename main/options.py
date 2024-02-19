from __future__ import annotations
from argparse import Namespace
from enum import Enum, IntEnum, auto
from data.general.roots import Roots
from main.args import _get_arguments
from main.log import log_error
from main.config import config
from process.general.const import AAPAaction

class ArgumentsException(Exception): pass

class AAPAProcessingOptions:
    """ Processing opties, opties over welke acties uit te voeren; ook de manier waarop uit te voeren kan worden beinvloed."""
    class INPUTOPTIONS(Enum):
        """ enum voor keuzes bij input van aanvragen 

            SCAN: scan een op te geven invoerdirectory (of de root-directory) voor nieuwe aanvragen.
            EXCEL: lees een op te geven Excel-file voor nieuwe aanvragen.

        """
        SCAN= auto()
        EXCEL=auto()
        def __str__(self):
            _AS_STRS = {AAPAProcessingOptions.INPUTOPTIONS.SCAN: 'Scan directory (PDF-files)', 
                        AAPAProcessingOptions.INPUTOPTIONS.EXCEL: 'Import from MS-FORMS Excel-file',
            }
            return _AS_STRS[self]
        @staticmethod
        def summary(values: set[AAPAProcessingOptions.INPUTOPTIONS])->str:
            return ",".join([str(option) for option in values])        
        @staticmethod
        def from_str(s: str)->set[AAPAProcessingOptions.INPUTOPTIONS]:
            result = set()
            if s:
                for ch in s.upper():
                    match ch:
                        case 'S': result.add(AAPAProcessingOptions.INPUTOPTIONS.SCAN)
                        case 'F': result.add(AAPAProcessingOptions.INPUTOPTIONS.EXCEL)
                        case _: log_error(f'Ongeldige waarde voor input_options: {ch}. Geldige waarden zijn S en F. Wordt genegeerd.' )
            return result
    class PROCESSINGMODE(IntEnum):
        """ enum voor de processing-mode.

            AANVRAGEN: verwerk aanvragen.
            VERSLAGEN: verwerk verslagen.   

        """
        AANVRAGEN= auto()
        VERSLAGEN =auto()
        def __str__(self):
            _AS_STRS = {AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN: 'Verwerk aanvragen', 
                        AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN: 'Verwerk verslagen',
            }
            return _AS_STRS[self]
        @staticmethod
        def summary(values: set[AAPAProcessingOptions.PROCESSINGMODE])->str:
            return ",".join([str(option) for option in values])        
        @staticmethod
        def from_str(s: str)->set[AAPAProcessingOptions.PROCESSINGMODE]:
            result = set()
            if s:
                for ch in s.upper():
                    match ch:
                        case 'A': result.add(AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN)
                        case 'V': result.add(AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN)
                        case _: log_error(f'Ongeldige waarde voor processing_mode: {ch}. Geldige waarden zijn A en V. Wordt genegeerd.' )
            return result
    
    def __init__(self, actions: list[AAPAaction]=[], preview = False, force=False, debug=False, input_options={INPUTOPTIONS.EXCEL}, processing_mode = {PROCESSINGMODE.AANVRAGEN}, onedrive=None):
        """ 
        parameters
        ----------
        actions: een of meer acties om uit te voeren. Zie AAPAAction voor de mogelijkheden. 
            Meerdere acties kunnen worden opgegeven.
        preview: Indien True: operaties worden niet werkelijk doorgevoerd maar wel op de console aangegeven.
        force: Indien True: reinitializatie van de database zonder verificatievraag.
        debug: Indien True: debugging mode.
        input_options: de input opties (zie INPUTOPTIONS voor de mogelijkheden)
            Meerdere opties kunnen worden opgegeven.
        processing_mode: de processing mode. (zie PROCESSINGMODE voor de mogelijkheden)
            Meerdere opties kunnen worden opgegeven.
        onedrive: alternatieve onedrive root. Debugging optie om op een kopie van de echte Sharepoint OneDrive te kunnen werken. 

        deze parameters worden opgeslagen in de gelijknamige attributen.

        """
        self.actions = actions
        self.input_options:set[self.INPUTOPTIONS] = input_options
        self.processing_mode:set[self.PROCESSINGMODE] = processing_mode
        self.preview = preview
        self.force   = force
        self.debug   = debug
        self.onedrive = onedrive
        if not self.actions:
            self.actions = [AAPAaction.NONE]
    def __str__(self):
        result = f'ACTIONS: {AAPAaction.get_actions_str(self.actions)}\n'
        result = result + f'INPUT OPTIONS: {self.INPUTOPTIONS.summary(self.input_options)}'
        result = result + f'PROCESSING MODE: {self.PROCESSINGMODE.summary(self.processing_mode)}'
        result = result + f'PREVIEW MODE: {self.preview}\n'
        result = result + f'DEBUG: {self.debug}  FORCE: {self.force}\n'
        if self.onedrive: 
            result = result + f'ONEDRIVE ROOT: {self.onedrive}\n'
        return result + '.'
    @classmethod
    def from_args(cls, args: Namespace)->AAPAProcessingOptions:
        """initializeer instantie vanuit een Namespace (resultaat van ArgumentParser.Parse)"""
        def _get_actions(actions: list[str])->list[AAPAaction]:
            result = []
            for action in actions: 
                if a := AAPAaction.from_action_choice(action):
                    result.append(a)
            return result
        return cls(actions=_get_actions(args.actions) if 'actions' in args else [], preview=args.preview, 
                   input_options = AAPAProcessingOptions.INPUTOPTIONS.from_str(args.input_options),
                   processing_mode= AAPAProcessingOptions.PROCESSINGMODE.from_str(args.processing_mode),
                   force=args.force, debug=args.debug, onedrive=args.onedrive)
    def no_processing(self, plugin=False)->bool:
        return not plugin and not any([a in self.actions for a in {AAPAaction.INPUT,AAPAaction.FORM, AAPAaction.MAIL, AAPAaction.UNDO, AAPAaction.FULL, AAPAaction.REPORT}])

class AAPAConfigOptions:
    """ Configuratie-gerelateerde opties. Directories, database en dergelijke. """
    def __init__(self, root_directory: str, output_directory: str, bbinput_directory: str, database_file: str, 
                 config_file:str=None, report_filename: str=None, excel_in: str=None):
        """      
        parameters
        ----------
        root_directory: de te gebruiken root directory. Dit is de "basis-directory" voor de te verwerken aanvragen en verslagen.
        output_directory: de directory waarin uitvoer wordt gegenereerd. Met name is dit voor beoordelingsformulieren van aanvragen.
        database_file: de te gebruiken SQLite database file.
        bbinput_directory: de directory waarin Blackboard zip-files met te importeren verslagen worden gezocht.
        config_file: de configuratiefile (alternatieve aapa_config.ini).
        report_filename: default filename voor rapportages.
        excel_in: default filename voor excel-import van aanvragen.

        deze parameters worden opgeslagen in de gelijknamige attributen.
        
        """
        def get_default(param: str, config_key: str)->str:
            return param if param is not None else config.get('configuration', config_key)
        self.root_directory: str = get_default(root_directory, 'root')
        self.output_directory: str = get_default(output_directory, 'output')
        self.database_file: str = get_default(database_file, 'database')
        self.bbinput_directory: str = get_default(bbinput_directory, 'bbinput')
        self.config_file: str = config_file
        self.report_filename: str = get_default(report_filename, 'filename')
        self.excel_in: str = get_default(excel_in, 'input')
    def __str__(self):
        result = f'CONFIGURATION:\n'
        if self.root_directory is not None:
            result = result + f'ROOT DIRECTORY: {self.root_directory}\n'
        if self.output_directory is not None:
            result = result + f'FORMULIEREN naar directory: {self.output_directory}\n'
        if self.database_file:
            result = result + f'DATABASE: {self.database_file}\n'
        if self.bbinput_directory is not None:
            result = result + f'BLACKBOARD input directory: {self.bbinput_directory}\n'
        if self.config_file: 
            result = result + f'laad alternatieve CONFIGURATIE {self.config_file}\n'
        if self.report_filename: 
            result = result + f'FILENAME (voor REPORT): {self.report_filename}\n'
        if self.excel_in: 
            result = result + f'FILENAME (voor SCAN input): {self.excel_in}\n'
        return result + '.'
    @classmethod
    def from_args(cls, args: Namespace)->AAPAConfigOptions:
        """initializeer instantie vanuit een Namespace (resultaat van ArgumentParser.Parse)"""
        return cls(root_directory = args.root, output_directory = args.output, bbinput_directory=args.bbinput, database_file = args.database, 
                   config_file = args.config, report_filename = args.report_file,# migrate_dir=args.migrate, 
                   excel_in=args.excel_in)


class AAPAOptions:
    """ De opties om het programma mee te besturen. """
    @staticmethod
    def _recode_for_onedrive(config_options: AAPAConfigOptions, onedrive_root: str):     
        """ Correct the onedrive-root: 
            at initialization the override to the OneDrive code in the config file is decoded with the 'real' onedrive, this must be corrected
        """   
        def _recode(obj: object, attribute: str, onedrive_root: str):
        
            setattr(obj, attribute, Roots.decode_onedrive(Roots.encode_onedrive(getattr(obj,attribute)), onedrive_root))
        _recode(config_options, 'root_directory', onedrive_root)
        _recode(config_options, 'output_directory', onedrive_root)
        _recode(config_options, 'database_file', onedrive_root)
        _recode(config_options, 'excel_in', onedrive_root)
    def __init__(self, 
                 config_options: AAPAConfigOptions = None, 
                 processing_options: AAPAProcessingOptions = None, 
                 ):
        """ 
        parameters
        ----------
        config_options: AAPAConfigOptions. 
            Opties voor de configuratie (directories en database). Zie AAPAConfigOptions voor meer.
        processing_options: AAPAProcessingOptions. 
            Opties voor de processing. Zie AAPAProessingOptions voor meer.

        De parameters worden opgeslagen in de gelijknamige attributen.

        Indien processing_options.onedrive: past ook de config_options aan voor deze onedrive parameter.

        """
        if processing_options.onedrive: 
            self._recode_for_onedrive(config_options, processing_options.onedrive)
        self.config_options = config_options
        self.processing_options = processing_options
    def __str__(self):
        return f'{str(self.config_options)}\n{str(self.processing_options)}'
    @classmethod
    def from_args(cls, args: Namespace)->AAPAOptions:
        """initializeer instantie vanuit een Namespace (resultaat van ArgumentParser.Parse)"""
        return cls(config_options = AAPAConfigOptions.from_args(args), 
                   processing_options = AAPAProcessingOptions.from_args(args),
                   )

def report_options(options: AAPAOptions, parts=0)->str:
    DEFAULT = "<default>:"
    QUERY   = "<to be queried>"
    def __report_str(item: str, attr, default):
        default_str = f'{DEFAULT} ({default})'
        return f'{item.upper()}: {str(attr) if attr else default_str}\n'
    def _report_str(item: str, attr, default=DEFAULT):
        if default != DEFAULT and attr == '':
            return __report_str(item, attr, QUERY)
        else:
            return __report_str(item, attr, default)
    result = ''
    config_options = options.config_options
    processing_options = options.processing_options
    if not (config_options or processing_options):
        return result
    if parts == 0 or parts == 2:
        result += _report_str('actions', AAPAaction.get_actions_str(processing_options.actions))    
        result += f'preview: {processing_options.preview}\n'
    if parts == 0 or parts == 1:
        result += _report_str('root directory', config_options.root_directory, config.get('configuration', 'root'))
        result +=  _report_str('forms directory', config_options.output_directory, config.get('configuration', 'output'))
        result +=  _report_str('database', config_options.database_file, config.get('configuration', 'database'))        
        if config_options.excel_in:
            result +=  _report_str('excel input file', config_options.excel_in, config.get('configuration', 'input'))        

    if parts == 1: 
        return result
    if parts == 0 or parts == 2:
        if AAPAaction.REPORT in processing_options.actions:
            result +=  _report_str('create report', str(config_options.report_filename))
        if config_options.config_file:
            result += _report_str('load alternative configuration file', config_options.config_file)
    return result


class ArgumentOption(Enum):
    CONFIG = auto()
    PROCES = auto()
    ALL    = auto()

def _get_options_from_commandline(args: dict, which: ArgumentOption=ArgumentOption.ALL)->type[AAPAConfigOptions | AAPAProcessingOptions | tuple[AAPAConfigOptions,AAPAProcessingOptions]]:
    """ Helper functie voor get_options_from_commandline.

        Doet het eigenlijke werk (verwerken van de met ArgumentParser.parse geparsede command-line arguments)
        Als losse functie ook beschikbaar voor custom functionaliteit.

    """
    match which:
        case ArgumentOption.CONFIG:
            return AAPAConfigOptions.from_args(args)
        case ArgumentOption.PROCES:
            return AAPAProcessingOptions.from_args(args)
        case ArgumentOption.ALL:
            return (AAPAConfigOptions.from_args(args),
                    AAPAProcessingOptions.from_args(args),
                    )               

def get_options_from_commandline(which: ArgumentOption=ArgumentOption.ALL)->type[AAPAConfigOptions | AAPAProcessingOptions | tuple[AAPAConfigOptions,AAPAProcessingOptions]]:
    """ Lees de commando-regel opties, parse deze, en geef deze terug in de vorm van AAPAoptions
    
    parameters
    ----------
    which: ArgumentOption
        ArgumentOption.ALL: geef alle ingevoerde opties terug in tuple-vorm: (AAPAConfigOptions, AAPAProcessingOptions)
            deze kunnen apart worden gebruikt of voor het initialiseren van AAPAOptions 
            (options = AAPAOptions(*get_options_from_command_line(ArgumentOption.ALL))
        ArgumentOption.CONFIG: geef alleen de AAPAConfigOptions
        ArgumentOption.PROCES: geef alleen de AAPAProcesOptions

    returns
    -------
    De gevraagde opties, in de vorm van een tuple indien meerdere gevraagd zijn.
    """
    try:
        args = _get_arguments()
        return _get_options_from_commandline(args, which)
    except IndexError as E:
        print(f'Ongeldige opties aangegeven: {E}.')   
        return None

if __name__=="__main__":
    args = _get_arguments()
    print(args)
    (config_options,processing_options) = get_options_from_commandline()
    if config_options: 
        print(str(config_options))
    if processing_options: 
        print(str(processing_options))
    print(report_options(AAPAOptions.from_args(args)))