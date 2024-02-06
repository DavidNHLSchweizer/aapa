from __future__ import annotations
from enum import Enum, auto

import gettext
from data.roots import Roots
from general.log import log_error
from general.versie import banner
def __vertaling(Text):
    # dit is de enige manier (voor zover bekend) om teksten in de 'usage' aanroep (aapa.py --help)
    # in het Nederlands te vertalen
    Text = Text.replace('usage', 'aanroep')
    Text = Text.replace('positional arguments', 'positionele argumenten')
    Text = Text.replace('options', 'opties')
    Text = Text.replace('show this help message and exit', 'Laat dit bericht zien en beeindig het programma.')
    return Text
gettext.gettext = __vertaling
import argparse

from general.config import config

class ArgumentsException(Exception): pass

class AAPAaction(Enum):
    """ Acties om uit te voeren.

    NONE: geen actie.
    INPUT: Verwerk input. 
        Voor aanvragen: importeer nieuwe aanvragen. 
        Voor rapporten: importeer nieuwe rapporten.
        Welke hiervan wordt uitgevoerd wordt bepaald door de processing_mode.
        Zie AAPAProcessingOptions.PROCESSINGMODE voor meer info.
    FORM: Maak nieuwe beoordelingsformulieren.
        Ook dit kan worden gedaan voor aanvragen en/of rapporten,
        afhankelijk van de processing_mode.
    MAIL: Lees beoordelingen en zet concept-mails klaar.
    FULL: combinatie van INPUT,FORM en MAIL.
    NEW: maak een nieuwe database aan. Indien de database al bestaat: maak de database leeg.
    INFO: druk de configuratie-informatie af op de console.
    REPORT: maak een aanvragen-rapportage (Aanvragen.XLSX).
    UNDO: maak de vorige actie ongedaan. 

    """
    NONE      = 0
    INPUT     = auto()
    FORM      = auto()
    MAIL      = auto()
    FULL      = auto()
    NEW       = auto()
    INFO      = auto()
    REPORT    = auto()
    UNDO      = auto()
    def help_str(self):
        match self:
            case AAPAaction.NONE: return 'Geen actie [DEFAULT]'
            case AAPAaction.INPUT: return 'Vind en importeer nieuwe aanvragen of verslagen (zie ook --input_options, --input_mode)'
            case AAPAaction.FORM: return 'Maak beoordelingsformulieren'
            case AAPAaction.MAIL: return 'Vind en verwerk beoordeelde aanvragen en zet feedbackmails klaar'
            case AAPAaction.FULL: return 'Volledig proces: scan + form + mail'
            case AAPAaction.NEW: return 'Maak een nieuwe database of verwijder alle data uit de database (als deze reeds bestaat).'
            case AAPAaction.INFO: return 'Laat configuratie (directories en database) zien'
            case AAPAaction.REPORT: return 'Rapporteer alle aanvragen in een .XLSX-bestand'
            case AAPAaction.UNDO: return 'Ongedaan maken van de laatste procesgang'
            case _: return ''
    @staticmethod
    def all_help_str():
        return '\n'.join([f'   {str(a)}: {a.help_str()}' for a in AAPAaction]) + \
                f'\nDefault is {str(AAPAaction.NONE)}.'
    def __str__(self):    
        return self.name.lower()
    @staticmethod
    def get_choices():
        return [str(a) for a in AAPAaction]
    @staticmethod
    def get_actions_str(actions: list[AAPAaction]):
        return '+'.join([str(a) for a in actions])
    @staticmethod
    def from_action_choice(action_choice: str)->AAPAaction:
        for a in AAPAaction:
            if str(a) == action_choice:
                return a
        return None

def _get_processing_arguments(parser: argparse.ArgumentParser,include_actions=True):
    if include_actions:
        parser.add_argument('actions', metavar='actie(s)', nargs='*', type=str, choices=AAPAaction.get_choices(), default='none',
                        help=f'Uit te voeren actie(s). Kan een of meer zijn van  {AAPAaction.get_choices()}.\nWanneer geen actie wordt opgegeven wordt als default "none" gebruikt (in preview-mode).\n{AAPAaction.all_help_str()}')    
    parser.add_argument('-preview', action='store_true', help='Preview-mode: Laat zien welke bestanden zouden worden bewerkt, maar voer de bewerkingen niet uit.\nEr worden geen nieuwe bestanden aangemaakt en de database wordt niet aangepast.')
    parser.add_argument('-force', action='store_true', dest='force', help=argparse.SUPPRESS) #forceer new database zonder vragen (ingeval action NEW)
    parser.add_argument('-debug', action='store_true', dest='debug', help=argparse.SUPPRESS) #forceer debug mode in logging system
    parser.add_argument('-io', '--input_options', type=str, choices=['S','F', 'SF'], default='S',help='Input opties: een of meer van "S" (scan directory), "F" (Forms-Excel file [default]).\nVoorbeeld: "--input_options=SF".')
    parser.add_argument('-pm', '--processing_mode', type=str, choices=['A','R', 'AR'], default='A',help='Processing mode: een of meer van "A" (aanvragen [default]), "R" (Rapporten).\nVoorbeeld: "--processing_mode=R".')
    parser.add_argument('-od', '--onedrive', type=str, help=argparse.SUPPRESS) # simulates the OneDrive root for debugging purposes

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
    class PROCESSINGMODE(Enum):
        """ enum voor de processing-mode.

            AANVRAGEN: verwerk aanvragen.
            RAPPORTEN: verwerk rapporten.   

        """
        AANVRAGEN= auto()
        RAPPORTEN =auto()
        def __str__(self):
            _AS_STRS = {AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN: 'Verwerk aanvragen', 
                        AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN: 'Verwerk rapporten',
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
                        case 'R': result.add(AAPAProcessingOptions.PROCESSINGMODE.RAPPORTEN)
                        case _: log_error(f'Ongeldige waarde voor processing_mode: {ch}. Geldige waarden zijn A en R. Wordt genegeerd.' )
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
    def from_args(cls, args: argparse.Namespace)->AAPAProcessingOptions:
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
    def no_processing(self)->bool:
        return not any([a in self.actions for a in {AAPAaction.INPUT,AAPAaction.FORM, AAPAaction.MAIL, AAPAaction.UNDO, AAPAaction.FULL, AAPAaction.REPORT}])

def _get_config_arguments(parser: argparse.ArgumentParser):
    group = parser.add_argument_group('configuratie opties')
    group.add_argument('-r', '--root', type=str, 
                        help='De rootdirectory voor het opslaan van nieuwe aanvragen of rapporten.\nAls geen directory wordt ingevoerd (-r=) wordt deze opgevraagd.')
    group.add_argument('-o', '--output', dest='output',  type=str, 
                        help='De directory voor het aanmaken en invullen van beoordelingsformulieren.\nAls geen directory wordt ingevoerd (-o=) wordt deze opgevraagd.')
    group.add_argument('-bb', '--bbinput', dest='bbinput',  type=str, 
                        help='De directory waar Blackboard .ZIP-files (voor invoer rapporten) worden gelezen.\nAls geen directory wordt ingevoerd (-bb=) wordt deze opgevraagd.')
    group.add_argument('-d', '--database', type=str, help='De naam van de databasefile om mee te werken.\nAls de naam niet wordt ingevoerd (-d=) wordt hij opgevraagd.\nIndien de databasefile niet bestaat wordt hij aangemaakt.')   
    group.add_argument('-rf', '--report_file', type=str, help='Bestandsnaam [.xlsx] voor actie "report". default: uit CONFIG.INI')
    group.add_argument('-x', '--excel_in', type=str, help='Bestandsnaam [.xlsx] voor actie "input" vanuit excel-bestand. Moet worden ingevoerd voor deze actie.')
    group.add_argument('-c', '--config', type=str, help='Laad een alternatieve configuratiefile. Aangenomen wordt dat dit een .INI bestand is.')
    # group.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 

class AAPAConfigOptions:
    """ Configuratie-gerelateerde opties. Directories, database en dergelijke. """
    def __init__(self, root_directory: str, output_directory: str, bbinput_directory: str, database_file: str, 
                 config_file:str=None, report_filename: str=None, excel_in: str=None):
        """      
        parameters
        ----------
        root_directory: de te gebruiken root directory. Dit is de "basis-directory" voor de te verwerken aanvragen en rapporten.
        output_directory: de directory waarin uitvoer wordt gegenereerd. Met name is dit voor beoordelingsformulieren van aanvragen.
        database_file: de te gebruiken SQLite database file.
        bbinput_directory: de directory waarin Blackboard zip-files met te importeren rapporten worden gezocht.
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
    def from_args(cls, args: argparse.Namespace)->AAPAConfigOptions:
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
    def from_args(cls, args: argparse.Namespace)->AAPAOptions:
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

def _init_parser():
    return argparse.ArgumentParser(description=banner(), prog='aapa', usage='%(prog)s [actie(s)] [opties]', formatter_class=argparse.RawTextHelpFormatter)

def aapa_parser(parser: argparse.ArgumentParser=None, include_actions=True)->argparse.ArgumentParser:
    """ aapa_parser: voegt alle AAPA-opties toe aan een bestaande ArgumentParser

    parameters
    ----------
    parser: ArgumentParser om opties aan toe te voegen, eerder geinitializeerd.
        Als parser is None wordt een nieuwe parser aangemaakt.
    include_actions: Indien True worden de AAPA actions (zie AAPAProcessingOptions) toegevoegd.
        Indien False gebeurt dat niet

    returns
    -------
    ArgumentParser met alle AAPA opties toegevoegd.

    Hiermee kunnen custom parsers (zie ook module extra) gebruik maken van de standaard AAPA opties.

"""
    if not parser:
        parser = _init_parser()
    _get_processing_arguments(parser, include_actions=include_actions)
    _get_config_arguments(parser)    
    return parser

def _get_arguments(command_line_arguments:list[str]=None):
    parser = _init_parser()
    aapa_parser(parser)
    return parser.parse_args(command_line_arguments)

def get_debug()->bool:
    return _get_arguments().debug

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