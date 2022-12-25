from __future__ import annotations
import argparse
from dataclasses import dataclass
from enum import Enum
from general.config import config

class ProcessMode(Enum):
    PROCESS = 0
    SCAN    = 1
    MAIL    = 2
    PREVIEW = 3
    def help_str(self):
        match self:
            case ProcessMode.PROCESS: return 'Verwerk alle (nieuwe) bestanden (combinatie SCAN en MAIL) [DEFAULT]'
            case ProcessMode.SCAN: return 'Vind en verwerk alleen nieuwe aanvragen (niet beoordeelde aanvragen en mail)'
            case ProcessMode.MAIL: return 'Vind en verwerk beoordeelde aanvragen (geen scan voor nieuwe aanvragen)'
            case ProcessMode.PREVIEW: return 'Laat te bewerken bestanden zien maar voer geen bewerkingen uit.'
            case _: return ''
        
    def __str__(self):    
        return self.name.lower()
    @staticmethod
    def get_choices():
        return [str(pm) for pm in ProcessMode]
    @staticmethod
    def from_mode_choice(mode_choice: str)->ProcessMode:
        for pm in ProcessMode:
            if str(pm) == mode_choice:
                return pm
        return None

def _get_arguments(banner: str):
    parser = argparse.ArgumentParser(description=banner)

    group = parser.add_argument_group('Configuratie, directory en database')
    group.add_argument('-r', '--root', type=str, 
                        help='Kies nieuwe directory als basis voor het scannen naar aanvragen. Als geen directory wordt ingevoerd (-r=) wordt deze opgevraagd.')
    group.add_argument('-f', '--formulieren', dest='forms',  type=str, 
                        help='Kies nieuwe directory voor beoordelingsformulieren. Als geen directory wordt ingevoerd (-f=) wordt deze opgevraagd.')
    group.add_argument('-m', '--mail', type=str, 
                        help='Kies nieuwe directory voor mailbestanden. Als geen directory wordt ingevoerd (-m=) wordt deze opgevraagd.')
    group.add_argument('-data', '--database', type=str, help='Gebruik een andere database met de opgegeven naam. Indien deze niet bestaat wordt hij aangemaakt, anders wordt hij geopend.')
    
    group = parser.add_argument_group('Acties en overige opties')
    group.add_argument('-mo', '--mode', default='process', choices=ProcessMode.get_choices(),
                        help='Keuze activiteit: ' + ', '.join([f'"{str(pm)}"-{ProcessMode.help_str(pm)}' for pm in ProcessMode]))
    group.add_argument('-init', action='store_true', dest='init', help= 'Initialiseer de database. Alle data wordt (na bevestiging) verwijderd. ')
    group.add_argument('-init!', action='store_true', dest='init_force', help= 'Initialiseer de database. Alle data wordt verwijderd. Er wordt geen bevestiging gevraagd.')
    group.add_argument('-info', action='store_true', help='Print configuration information')
    group.add_argument('-x', '--xlsx', type=str, help='Rapporteer aanvragen in een .XSLX bestand. Indien geen bestandsnaam wordt ingevoerd (-x=) gaat alleen een samenvatting naar de console.')
    group.add_argument('-clean',  action='store_true', help='Verwijder overbodige bestanden van verwerkte aanvragen.')
    # group.add_argument('-noscan', action='store_true', help='Scan niet op nieuwe aanvragen.')
    # group.add_argument('-nomail', action='store_true', help='Beoordeelde bestanden worden niet verwerkt.')
    # group.add_argument('-noact', action='store_true', help='Combinatie van -nomail en -noscan.')
    return parser.parse_args()

class Initialize(Enum):
    NO_INIT    = 0
    INIT       = 1
    INIT_FORCE = 2
    def __str__(self):
        match self:
            case Initialize.INIT: return 'initialiseer database'
            case Initialize.INIT_FORCE: return 'initialiseer database! (geen verificatievraag)'
            case _: return ''
@dataclass
class AAPAoptions:
    root: str = None
    forms: str= None
    mail: str= None
    database: str = config.get('database', 'database_name')
    mode: ProcessMode = ProcessMode.PROCESS
    initialize: Initialize = Initialize.NO_INIT
    report: str = None
    info: bool = False
    clean: bool = False
    # noscan: bool = False
    # nomail: bool = False
    def __str__(self):
        result = ''
        if self.root is not None:
            result = result + f'root directory: {self.root}\n'
        if self.forms is not None:
            result = result + f'beoordelingsformulieren naar directory: {self.forms}\n'
        if self.mail is not None:
            result = result + f'mailbestanden naar directory: {self.mail}\n'
        if self.database:
            result = result + f'database: {self.database}\n'
        result = result + f'process mode: {self.mode}\n'
        if self.initialize != Initialize.NO_INIT: 
            result = result + f'{str(self.initialize)}\n'
        if self.report is not None:
            result = result + f'report: {self.report}\n'
        if self.info: 
            result = result + f'print configuration information\n'
        return result + f'clean: {self.clean}.'#  noscan: {self.noscan}  nomail: {self.nomail}.'

def report_options(options: AAPAoptions, config_only = False)->str:
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
    result += _report_str('root directory', options.root, config.get('configuration', 'root'))
    result +=  _report_str('forms directory', options.forms, config.get('configuration', 'forms'))
    result +=  _report_str('mail directory', options.mail, config.get('configuration', 'mail'))
    result +=  _report_str('database', options.database, config.get('configuration', 'database'))
    if config_only: 
        return result
    result += _report_str('process mode', str(options.mode))
    if options.initialize != Initialize.NO_INIT:
        result +=  _report_str('initialize database', str(options.initialize))
    if options.report:
        result +=  _report_str('create report', str(options.report))
    else:
        result +=  _report_str('create report', 'None')
    if options.info:
        result += f'print configuration info\n'
    return result + f'clean: {options.clean}.'# noscan: {options.noscan}  nomail: {options.nomail}.'

def get_arguments()->AAPAoptions:
    def get_init(args):
        if args.init: return Initialize.INIT
        elif args.init_force: return Initialize.INIT_FORCE
        else: return Initialize.NO_INIT
    try:
        args = _get_arguments('Als er geen opties worden gekozen wordt de huidige rootdirectory gescand op nieuwe aanvragen, en worden beoordeelde aanvragen verwerkt.')
        return AAPAoptions(root=args.root, forms=args.forms, mail=args.mail, database=args.database, mode = ProcessMode.from_mode_choice(args.mode), initialize=get_init(args), info=args.info, report=args.xlsx, clean=args.clean)
        # noscan=args.noscan or args.noact, nomail=args.nomail or args.noact)
    except IndexError as E:
        print(f'Ongeldige opties aangegeven: {E}.')   
        return None

if __name__=="__main__":
    if (options := get_arguments()):
        print(str(options))
        print(report_options(options))
    