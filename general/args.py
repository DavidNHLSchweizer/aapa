from __future__ import annotations
from enum import Enum

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
    MAIL     = 2
    FULL     = 3
    NEW      = 4
    INFO     = 5
    REPORT   = 6

    def help_str(self):
        match self:
            case AAPAaction.SCAN: return 'Vind en verwerk nieuwe aanvragen, maak beoordelingsformulieren'
            case AAPAaction.MAIL: return 'Vind en verwerk beoordeelde aanvragen en zet feedbackmails klaar'
            case AAPAaction.FULL: return 'Volledig proces: scan + mail'
            case AAPAaction.NEW: return 'Maak een nieuwe database of verwijder alle data uit de database (als deze reeds bestaat).'
            case AAPAaction.INFO: return 'Laat configuratie (directories en database) zien'
            case AAPAaction.REPORT: return 'Rapporteer alle aanvragen in een .XLSX-bestand'
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
    return parser.parse_args()


class AAPAoptions:
    def __init__(self, actions: list[AAPAaction], root_directory: str, forms_directory: str, database_file: str, 
                 preview = False, filename:str = None, config_file:str = None, history_file:str = None, diff_file:str = None):
        self.actions = actions
        self.root_directory = root_directory
        self.forms_directory: str= forms_directory
        self.database_file: str = database_file if database_file else config.get('configuration', 'database')
        self.preview: bool = preview
        if AAPAaction.REPORT in self.actions:
            self.filename: str = filename if filename else config.get('report', 'filename')
        else:
            self.filename: str = None
        self.config_file: str = config_file
        self.history_file: str = history_file
        self.diff_file: str = diff_file
    def __str__(self):
        result = f'ACTIONS: {AAPAaction.get_actions_str(self.actions)}\n'
        if self.root_directory is not None:
            result = result + f'ROOT DIRECTORY: {self.root_directory}\n'
        if self.forms_directory is not None:
            result = result + f'FORMULIEREN naar directory: {self.forms_directory}\n'
        if self.database_file:
            result = result + f'DATABASE: {self.database_file}\n'
        result = result + f'PREVIEW MODE: {self.preview}\n'
        if self.filename is not None:
            result = result + f'FILENAME (voor REPORT): {self.filename}\n'
        if self.config_file: 
            result = result + f'laad alternatieve CONFIGURATIE {self.config_file}\n'
        return result + '.'

def report_options(options: AAPAoptions, parts=0)->str:
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
    if not options:
        return result
    if parts == 0 or parts == 2:
        result += _report_str('actions', AAPAaction.get_actions_str(options.actions))    
        result += f'preview: {options.preview}\n'
    if parts == 0 or parts == 1:
        result += _report_str('root directory', options.root_directory, config.get('configuration', 'root'))
        result +=  _report_str('forms directory', options.forms_directory, config.get('configuration', 'forms'))
        result +=  _report_str('database', options.database_file, config.get('configuration', 'database'))
    if parts == 1: 
        return result
    if parts == 0 or parts == 2:
        if AAPAaction.REPORT in options.actions:
            result +=  _report_str('create report', str(options.filename))
        if options.config_file:
            result += _report_str('load alternative configuration file', options.config_file)
    return result

def get_arguments()->AAPAoptions:
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
        return AAPAoptions(actions=actions, root_directory=args.root, forms_directory=args.forms, database_file=args.database, 
                           preview=preview, filename=args.file, config_file=args.config, history_file=args.history, diff_file=args.difference)
    except IndexError as E:
        print(f'Ongeldige opties aangegeven: {E}.')   
        return None


if __name__=="__main__":
    args = _get_arguments()
    print(args)
    if (options := get_arguments()):
        print(str(options))
        print(report_options(options))
    