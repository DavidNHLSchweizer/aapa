from __future__ import annotations
from enum import Enum, auto

import gettext
from general.versie import banner
def __vertaling(Text):
    Text = Text.replace('usage', 'aanroep')
    Text = Text.replace('positional arguments', 'positionele argumenten')
    Text = Text.replace('options', 'opties')
    Text = Text.replace('show this help message and exit', 'Laat dit bericht zien en beeindig het programma.')
    return Text
gettext.gettext = __vertaling
import argparse

from general.config import config

class AAPAaction(Enum):
    SCAN     = 1
    FORM     = 2
    MAIL     = 3
    FULL     = 4
    NEW      = 5
    INFO     = 6
    REPORT   = 7
    UNDO     = 8
    ZIPIMPORT= 9

    def help_str(self):
        match self:
            case AAPAaction.SCAN: return 'Vind en importeer nieuwe aanvragen'
            case AAPAaction.FORM: return 'maak beoordelingsformulieren'
            case AAPAaction.MAIL: return 'Vind en verwerk beoordeelde aanvragen en zet feedbackmails klaar'
            case AAPAaction.FULL: return 'Volledig proces: scan + form + mail'
            case AAPAaction.NEW: return 'Maak een nieuwe database of verwijder alle data uit de database (als deze reeds bestaat).'
            case AAPAaction.INFO: return 'Laat configuratie (directories en database) zien'
            case AAPAaction.REPORT: return 'Rapporteer alle aanvragen in een .XLSX-bestand'
            case AAPAaction.UNDO: return 'Ongedaan maken van de laatste procesgang'
            case AAPAaction.ZIPIMPORT: return 'Importeren verslagen uit zipfile'
            case _: return ''
    @staticmethod
    def all_help_str():
        return '\n'.join([f'   {str(a)}: {a.help_str()}' for a in AAPAaction]) + \
                f'\nDefault is {str(AAPAaction.FULL)} (in preview-mode).'
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

def _get_arguments():
    parser = argparse.ArgumentParser(description=banner(), prog='aapa', usage='%(prog)s [actie(s)] [opties]', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('actions', metavar='actie(s)', nargs='*', type=str, choices=AAPAaction.get_choices(), default='full',
                        help=f'Uit te voeren actie(s). Kan een of meer zijn van  {AAPAaction.get_choices()}.\nWanneer geen actie wordt opgegeven wordt als default "full" gebruikt (in preview-mode).\n{AAPAaction.all_help_str()}')
    group = parser.add_argument_group('configuratie opties')
    group.add_argument('-r', '--root', type=str, 
                        help='De rootdirectory voor het scannen naar aanvragen.\nAls geen directory wordt ingevoerd (-r=) wordt deze opgevraagd.')
    group.add_argument('-f', '--forms', dest='forms',  type=str, 
                        help='De directory voor het aanmaken en invullen van beoordelingsformulieren.\nAls geen directory wordt ingevoerd (-f=) wordt deze opgevraagd.')
    group.add_argument('-d', '--database', type=str, help='De naam van de databasefile om mee te werken.\nAls de naam niet wordt ingevoerd (-d=) wordt hij opgevraagd.\nIndien de databasefile niet bestaat wordt hij aangemaakt.')   
    group = parser.add_argument_group('overige opties')
    group.add_argument('-c', '--config', type=str, help='Laad een alternatieve configuratiefile. Aangenomen wordt dat dit een .INI bestand is.')
    group.add_argument('-preview', action='store_true', help='Preview-mode: Laat zien welke bestanden zouden worden bewerkt, maar voer de bewerkingen niet uit.\nEr worden geen nieuwe bestanden aangemaakt en de database wordt niet aangepast.')
    group.add_argument('-file', '--file', type=str, help='Bestandsnaam [.xlsx] voor actie "report".')
    group.add_argument('--difference', dest='difference', type=str,help=argparse.SUPPRESS) #maak een verschilbestand voor een student (voer studentnummer in); "invisible" command; bv: --difference=diff.html
    group.add_argument('--history', dest='history', type=str,help=argparse.SUPPRESS) #voer beoordelingsgegevens in via een aangepast report-bestand; "invisible" command; bv: --history=history.xlsx
    group.add_argument('--reset', dest='reset', type=str,help=argparse.SUPPRESS) #voer code in voor het terugzetten van de status van een aanvraag. Zie documentatie voor mogelijkheden bv: --reset=mail:aanvraagnr
    group.add_argument('-force', action='store_true', dest='force', help=argparse.SUPPRESS) #forceer new database zonder vragen (ingeval action NEW)
    group.add_argument('-debug', action='store_true', dest='debug', help=argparse.SUPPRESS) #forceer debug mode in logging system
    return parser.parse_args()

class AAPAConfigOptions:
    def __init__(self, root_directory: str, output_directory: str, database_file: str, config_file:str = None, force=False, debug=False):
        self.root_directory = root_directory
        self.output_directory: str= output_directory
        self.database_file: str = database_file if database_file else config.get('configuration', 'database')
        self.config_file: str = config_file
        self.force: bool = force
        self.debug: bool = debug
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
        return result + '.'

class AAPAProcessingOptions:
    def __init__(self, actions: list[AAPAaction], preview = False, filename:str = None, history_file:str = None, diff_file:str = None):
        self.actions = actions
        self.preview: bool = preview
        if AAPAaction.REPORT in self.actions:
            self.filename: str = filename if filename else config.get('report', 'filename')
        else:
            self.filename: str = None
        self.history_file: str = history_file
        self.diff_file: str = diff_file
    def __str__(self):
        result = f'ACTIONS: {AAPAaction.get_actions_str(self.actions)}\n'
        result = result + f'PREVIEW MODE: {self.preview}\n'
        if self.filename is not None:
            result = result + f'FILENAME (voor REPORT): {self.filename}\n'
        return result + '.'

class AAPAOptions:
    def __init__(self, root_directory: str, output_directory: str, database_file: str, config_file:str = None,force=False, debug=False,
                 actions: list[AAPAaction] = [AAPAaction.FULL], preview = False, filename:str = None, history_file:str = None, 
                 diff_file:str = None):
        self.config_options = AAPAConfigOptions(root_directory=root_directory, output_directory=output_directory, database_file=database_file, 
                                                config_file=config_file, force=force, debug=debug)
        self.processing_options = AAPAProcessingOptions(actions=actions, preview=preview, filename=filename, history_file=history_file, diff_file=diff_file)

    def __str__(self):
        return f'{str(self.config_options)}\n{str(self.processing_options)}'

def report_options(config_options: AAPAConfigOptions, processing_options: AAPAProcessingOptions, parts=0)->str:
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
    if not (config_options or processing_options):
        return result
    if parts == 0 or parts == 2:
        result += _report_str('actions', AAPAaction.get_actions_str(processing_options.actions))    
        result += f'preview: {processing_options.preview}\n'
    if parts == 0 or parts == 1:
        result += _report_str('root directory', config_options.root_directory, config.get('configuration', 'root'))
        result +=  _report_str('forms directory', config_options.output_directory, config.get('configuration', 'forms'))
        result +=  _report_str('database', config_options.database_file, config.get('configuration', 'database'))
    if parts == 1: 
        return result
    if parts == 0 or parts == 2:
        if AAPAaction.REPORT in processing_options.actions:
            result +=  _report_str('create report', str(processing_options.filename))
        if config_options.config_file:
            result += _report_str('load alternative configuration file', config_options.config_file)
    return result

def get_debug()->bool:
    return _get_arguments().debug

class ArgumentOption(Enum):
    CONFIG = auto()
    PROCES = auto()
    BOTH   = auto()

def get_arguments(which: ArgumentOption)->type[AAPAConfigOptions | AAPAProcessingOptions | tuple[AAPAConfigOptions,AAPAProcessingOptions]]:
    def _get_actions(actions: list[str])->list[AAPAaction]:
        result = []
        for action in actions: 
            if a := AAPAaction.from_action_choice(action):
                result.append(a)
        return result
    try:
        args = _get_arguments()
        actions = _get_actions(args.actions)
        preview = args.preview
        if not actions:
            actions=[AAPAaction.FULL]
            preview = True
        match which:
            case ArgumentOption.CONFIG:
                return AAPAConfigOptions(root_directory=args.root, output_directory=args.forms, database_file=args.database, config_file=args.config, force=args.force, debug=args.debug)
            case ArgumentOption.PROCES:
                return AAPAProcessingOptions(actions=actions, preview=preview, filename=args.file, history_file=args.history, diff_file=args.difference)
            case ArgumentOption.BOTH:
                return (AAPAConfigOptions(root_directory=args.root, output_directory=args.forms, database_file=args.database, config_file=args.config, force=args.force, debug=args.debug),
                        AAPAProcessingOptions(actions=actions, preview=preview, filename=args.file, history_file=args.history, diff_file=args.difference))
                
    except IndexError as E:
        print(f'Ongeldige opties aangegeven: {E}.')   
        return None

if __name__=="__main__":
    args = _get_arguments()
    print(args)
    (config_options,processing_options) = get_arguments(ArgumentOption.BOTH)
    if config_options: 
        print(str(config_options))
    if processing_options: 
        print(str(processing_options))
    print(report_options(config_options, processing_options))
    