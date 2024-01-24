from __future__ import annotations
from enum import Enum, auto

import gettext
from data.roots import decode_onedrive, encode_onedrive
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
            case AAPAaction.INPUT: return 'Vind en importeer nieuwe aanvragen of verslagen (zie ook --input_options)'
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

def _get_processing_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('actions', metavar='actie(s)', nargs='*', type=str, choices=AAPAaction.get_choices(), default='none',
                        help=f'Uit te voeren actie(s). Kan een of meer zijn van  {AAPAaction.get_choices()}.\nWanneer geen actie wordt opgegeven wordt als default "none" gebruikt (in preview-mode).\n{AAPAaction.all_help_str()}')    
    parser.add_argument('-preview', action='store_true', help='Preview-mode: Laat zien welke bestanden zouden worden bewerkt, maar voer de bewerkingen niet uit.\nEr worden geen nieuwe bestanden aangemaakt en de database wordt niet aangepast.')
    parser.add_argument('-force', action='store_true', dest='force', help=argparse.SUPPRESS) #forceer new database zonder vragen (ingeval action NEW)
    parser.add_argument('-debug', action='store_true', dest='debug', help=argparse.SUPPRESS) #forceer debug mode in logging system
    parser.add_argument('-io', '--input_options', type=str, help='Input options: one or more of "S" (scan directory), "F" (Forms-Excel file), "B" (Blackboard zipfile).\nExample: "--input_options=SF".')
    parser.add_argument('-od', '--onedrive', type=str, help=argparse.SUPPRESS) # simulates the OneDrive root for debugging purposes

class AAPAProcessingOptions:
    class INPUTOPTIONS(Enum):
        SCAN= auto()
        EXCEL=auto()
        BBZIP=auto()
        def __str__(self):
            _AS_STRS = {AAPAProcessingOptions.INPUTOPTIONS.SCAN: 'Scan directory (PDF-files)', 
                        AAPAProcessingOptions.INPUTOPTIONS.EXCEL: 'Import from MS-FORMS Excel-file',
                        AAPAProcessingOptions.INPUTOPTIONS.BBZIP: 'Import ZIPfile(s) from Blackboard',}
            return _AS_STRS[self]
        @staticmethod
        def summary(values: set[AAPAProcessingOptions.INPUTOPTIONS])->str:
            return ",".join([str(option) for option in values])        
        @staticmethod
        def from_str(s: str)->set[AAPAProcessingOptions.INPUTOPTIONS]:
            result = set()
            for ch in s.upper():
                match ch:
                    case 'S': result.add(AAPAProcessingOptions.INPUTOPTIONS.SCAN)
                    case 'F': result.add(AAPAProcessingOptions.INPUTOPTIONS.EXCEL)
                    case 'B': result.add(AAPAProcessingOptions.INPUTOPTIONS.BBZIP)
                    case _: log_error(f'Ongeldige waarde voor input_options: {ch}. Geldige waarden zijn S, B, en F. Wordt genegeerd.' )
            return result
                    
    def __init__(self, actions: list[AAPAaction], preview = False, force=False, debug=False, input_options={INPUTOPTIONS.SCAN,INPUTOPTIONS.EXCEL}, onedrive=None):
        self.actions = actions
        self.input_options = input_options
        self.preview = preview
        self.force   = force
        self.debug   = debug
        self.onedrive = onedrive
        if not self.actions:
            self.actions = [AAPAaction.NONE]
    def __str__(self):
        result = f'ACTIONS: {AAPAaction.get_actions_str(self.actions)}\n'
        result = result + f'INPUT OPTIONS: {self.INPUTOPTIONS.summary(self.input_options)}'
        result = result + f'PREVIEW MODE: {self.preview}\n'
        result = result + f'DEBUG: {self.debug}  FORCE: {self.force}\n'
        if self.onedrive: 
            result = result + f'ONEDRIVE ROOT: {self.onedrive}\n'
        return result + '.'
    @classmethod
    def from_args(cls, args: argparse.Namespace)->AAPAProcessingOptions:
        def _get_actions(actions: list[str])->list[AAPAaction]:
            result = []
            for action in actions: 
                if a := AAPAaction.from_action_choice(action):
                    result.append(a)
            return result
        return cls(actions=_get_actions(args.actions), preview=args.preview, 
                   input_options = AAPAProcessingOptions.INPUTOPTIONS.from_str(args.input_options), 
                   force=args.force, debug=args.debug, onedrive=args.onedrive)
    def no_processing(self)->bool:
        return not any([a in self.actions for a in {AAPAaction.INPUT,AAPAaction.FORM, AAPAaction.MAIL, AAPAaction.UNDO, AAPAaction.FULL, AAPAaction.REPORT}])

def _get_config_arguments(parser: argparse.ArgumentParser):
    group = parser.add_argument_group('configuratie opties')
    group.add_argument('-r', '--root', type=str, 
                        help='De rootdirectory voor het opslaan van nieuwe aanvragen of rapporten.\nAls geen directory wordt ingevoerd (-r=) wordt deze opgevraagd.')
    group.add_argument('-o', '--output', dest='output',  type=str, 
                        help='De directory voor het aanmaken en invullen van beoordelingsformulieren.\nAls geen directory wordt ingevoerd (-o=) wordt deze opgevraagd.')
    group.add_argument('-d', '--database', type=str, help='De naam van de databasefile om mee te werken.\nAls de naam niet wordt ingevoerd (-d=) wordt hij opgevraagd.\nIndien de databasefile niet bestaat wordt hij aangemaakt.')   
    group.add_argument('-rf', '--report_file', type=str, help='Bestandsnaam [.xlsx] voor actie "report". default: uit CONFIG.INI')
    group.add_argument('-x', '--excel_in', type=str, help='Bestandsnaam [.xlsx] voor actie "input" vanuit excel-bestand. Moet worden ingevoerd voor deze actie.')
    group.add_argument('-c', '--config', type=str, help='Laad een alternatieve configuratiefile. Aangenomen wordt dat dit een .INI bestand is.')
    group.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 

class AAPAConfigOptions:
    def __init__(self, root_directory: str, output_directory: str, database_file: str, 
                 config_file:str=None, report_filename: str=None, migrate_dir: str=None, 
                 excel_in: str=None):
        def get_default(param: str, config_key: str)->str:
            return param if param is not None else config.get('configuration', config_key)
        self.root_directory: str = get_default(root_directory, 'root')
        self.output_directory: str = get_default(output_directory, 'output')
        self.database_file: str = get_default(database_file, 'database')
        self.config_file: str = config_file
        self.report_filename: str = get_default(report_filename, 'filename')
        self.migrate_dir: str = migrate_dir
        self.excel_in: str = get_default(excel_in, 'input')
    def __str__(self):
        result = f'CONFIGURATION:\n'
        if self.root_directory is not None:
            result = result + f'ROOT DIRECTORY: {self.root_directory}\n'
        if self.output_directory is not None:
            result = result + f'FORMULIEREN naar directory: {self.output_directory}\n'
        if self.database_file:
            result = result + f'DATABASE: {self.database_file}\n'
        if self.config_file: 
            result = result + f'laad alternatieve CONFIGURATIE {self.config_file}\n'
        if self.report_filename: 
            result = result + f'FILENAME (voor REPORT): {self.report_filename}\n'
        if self.migrate_dir:
            result = result + f'Directory voor SQL-data (gebruik in migratiescript): {self.migrate_dir}\n'
        if self.excel_in: 
            result = result + f'FILENAME (voor SCAN input): {self.excel_in}\n'
        return result + '.'
    @classmethod
    def from_args(cls, args: argparse.Namespace)->AAPAConfigOptions:
        return cls(root_directory = args.root, output_directory = args.output, database_file = args.database, 
                   config_file = args.config, report_filename = args.report_file, migrate_dir=args.migrate, 
                   excel_in=args.excel_in)

def _get_other_arguments(parser: argparse.ArgumentParser):
    group = parser.add_argument_group('overige opties')
    group.add_argument('--detect', dest='detect', type=str,help=r'Detecteer gegevens vanuit een directory bv: --detect=c:\users\david\NHL Stenden\...')
    group.add_argument('--difference', dest='difference', type=str,help=argparse.SUPPRESS) #maak een verschilbestand voor een student (voer studentnummer in); "invisible" command; bv: --difference=diff.html
    group.add_argument('--history', dest='history', type=str,help=argparse.SUPPRESS) #voer beoordelingsgegevens in via een aangepast report-bestand; "invisible" command; bv: --history=history.xlsx
    group.add_argument('--student', dest='student', type=str,help='Importeer gegevens over studenten uit Excel-bestand') 
    group.add_argument('--basedir', dest='basedir', type=str,help='Importeer gegevens voor nieuwe basedir(s) uit Excel-bestand')    

class AAPAOtherOptions:
    def __init__(self, detect_dir:str = None, diff_file:str = None, history_file:str = None,
                  student_file:str = None, basedir_file: str = None):
        self.detect_dir: str = detect_dir
        self.diff_file: str = diff_file
        self.history_file: str = history_file
        self.student_file: str = student_file
        self.basedir_file: str = basedir_file
    def __str__(self):
        result = f'OTHER OPTIONS:\n'
        if self.detect_dir is not None:
            result = result + f'DIRECTORY voor DETECT: {self.detect_dir}\n'
        if self.diff_file is not None:
            result = result + f'Student of zo om verschil te maken [#DEPRECATED]: {self.student_file}\n'
        if self.history_file is not None:
            result = result + f'Bestand voor laden history [#DEPRECATED]: {self.history_file}\n'
        if self.student_file is not None:
            result = result + f'Bestand voor studentgegevens: {self.student_file}\n'
        if self.basedir_file is not None:
            result = result + f'Bestand voor basedir-gegevens: {self.basedir_file}\n'
        return result + '.'
    def no_processing(self)->bool:
            return self.detect_dir is None and self.diff_file is None and self.history_file is None and self.student_file is None and self.basedir_file is None
    @classmethod
    def from_args(cls, args: argparse.Namespace)->AAPAOtherOptions:
        return cls(detect_dir = args.detect, diff_file = args.difference, history_file = args.history, 
                   student_file= args.student, basedir_file= args.basedir)

class AAPAOptions:
    def recode(self, obj: object, attribute: str, onedrive_root: str):
        # at initialization the override to the OneDrive code in the config file is decoded with the 'real' onedrive, this must be corrected
        setattr(obj, attribute, decode_onedrive(encode_onedrive(getattr(obj,attribute)), onedrive_root))
    def recode_for_onedrive(self, onedrive_root: str):
        self.recode(self.config_options, 'root_directory', onedrive_root)
        self.recode(self.config_options, 'output_directory', onedrive_root)
        self.recode(self.config_options, 'database_file', onedrive_root)
        self.recode(self.config_options, 'excel_in', onedrive_root)
    def __init__(self, 
                 config_options: AAPAConfigOptions = None, 
                 processing_options: AAPAProcessingOptions = None, 
                 other_options: AAPAOtherOptions = None):
        self.config_options = config_options
        self.processing_options = processing_options
        self.other_options = other_options      
        if processing_options.onedrive: 
            self.recode_for_onedrive(processing_options.onedrive)
    def __str__(self):
        return f'{str(self.config_options)}\n{str(self.processing_options)}\n{str(self.other_options)}'
    @classmethod
    def from_args(cls, args: argparse.Namespace)->AAPAOptions:
        return cls(config_options = AAPAConfigOptions.from_args(args), 
                   processing_options = AAPAProcessingOptions.from_args(args),
                   other_options = AAPAOtherOptions.from_args(args)
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
    other_options = options.other_options
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
        if other_options.detect_dir:
            result += _report_str('detect from directory', other_options.detect_dir)
        if other_options.student_file:
            result += _report_str('load student data', other_options.student_file)
        if other_options.basedir_file:
            result += _report_str('load basedir data', other_options.basedir_file)
        if config_options.config_file:
            result += _report_str('load alternative configuration file', config_options.config_file)
    return result

def _copy_parser(parser: argparse.ArgumentParser):
    """
    Als losse functie beschikbaar: vult een gegeven parser aan met alle parsing opties. 
    Hiermee kunnen custom parsers gebruik maken van de standaard AAPA opties (zie remove_aanvraag.py)
    """
    _get_processing_arguments(parser)
    _get_config_arguments(parser)    
    _get_other_arguments(parser)

def _get_arguments(command_line_arguments:list[str]=None):
    parser = argparse.ArgumentParser(description=banner(), prog='aapa', usage='%(prog)s [actie(s)] [opties]', formatter_class=argparse.RawTextHelpFormatter)
    _copy_parser(parser)
    return parser.parse_args(command_line_arguments)

def get_debug()->bool:
    return _get_arguments().debug

class ArgumentOption(Enum):
    CONFIG = auto()
    PROCES = auto()
    OTHER  = auto()
    ALL    = auto()

def _get_options_from_commandline(args: dict, which: ArgumentOption=ArgumentOption.ALL)->type[AAPAConfigOptions | AAPAProcessingOptions | tuple[AAPAConfigOptions,AAPAProcessingOptions,AAPAOtherOptions]]:
    """
    Helper functie voor get_options_from_commandline
    Doet het eigenlijke werk (verwerken van de met ArgumentParser.parse geparsede command-line arguments)
    Als losse functie ook beschikbaar voor custom functionaliteit (zie remove_aanvraag.py)
    """
    match which:
        case ArgumentOption.CONFIG:
            return AAPAConfigOptions.from_args(args)
        case ArgumentOption.PROCES:
            return AAPAProcessingOptions.from_args(args)
        case ArgumentOption.OTHER:
            return AAPAOtherOptions.from_args(args)
        case ArgumentOption.ALL:
            return (AAPAConfigOptions.from_args(args),
                    AAPAProcessingOptions.from_args(args),
                    AAPAOtherOptions.from_args(args))               

def get_options_from_commandline(which: ArgumentOption=ArgumentOption.ALL)->type[AAPAConfigOptions | AAPAProcessingOptions | tuple[AAPAConfigOptions,AAPAProcessingOptions,AAPAOtherOptions]]:
    """
    Lees de commando-regel opties, parse deze, en geef deze terug in de vorm van AAPAoptions
    
    parameters:
    which: ArgumentOption
        ArgumentOption.ALL: geef alle ingevoerde opties terug in tuple-vorm: (AAPAConfigOptions, AAPAProcessingOptions, AAPAOtherOptions)
            deze kunnen apart worden gebruikt of voor het initialiseren van AAPAOptions 
                (options = AAPAOptions(*get_options_from_command_line(ArgumentOption.ALL))
        ArgumentOption.CONFIG: geef alleen de AAPAConfigOptions
        ArgumentOption.PROCES: geef alleen de AAPAProcesOptions
        ArgumentOption.OTHER: geef alleen de AAPAOtherOptions
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
    (config_options,processing_options,other_options) = get_options_from_commandline()
    if config_options: 
        print(str(config_options))
    if processing_options: 
        print(str(processing_options))
    if other_options: 
        print(str(other_options))
    print(report_options(AAPAOptions.from_args(args)))