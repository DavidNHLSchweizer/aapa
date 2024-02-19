from __future__ import annotations
import gettext
from main.versie import banner
from process.general.const import AAPAaction
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

def _get_processing_arguments(parser: argparse.ArgumentParser,include_actions=True):
    if include_actions:
        parser.add_argument('actions', metavar='actie(s)', nargs='*', type=str, choices=AAPAaction.get_choices(), default='none',
                        help=f'Uit te voeren actie(s). Kan een of meer zijn van  {AAPAaction.get_choices()}.\nWanneer geen actie wordt opgegeven wordt als default "none" gebruikt (in preview-mode).\n{AAPAaction.all_help_str()}')    
    parser.add_argument('-preview', action='store_true', help='Preview-mode: Laat zien welke bestanden zouden worden bewerkt, maar voer de bewerkingen niet uit.\nEr worden geen nieuwe bestanden aangemaakt en de database wordt niet aangepast.')
    parser.add_argument('-force', action='store_true', dest='force', help=argparse.SUPPRESS) #forceer new database zonder vragen (ingeval action NEW)
    parser.add_argument('-debug', action='store_true', dest='debug', help=argparse.SUPPRESS) #forceer debug mode in logging system
    parser.add_argument('-io', '--input_options', type=str, choices=['S','F', 'SF'], default='F',help='Input opties: een of meer van "S" (scan directory), "F" (Forms-Excel file [default]).\nVoorbeeld: "--input_options=SF".')
    parser.add_argument('-pm', '--processing_mode', type=str, choices=['A','V', 'AV'], default='A',help='Processing mode: een of meer van "A" (aanvragen [default]), "V" (Verslagen).\nVoorbeeld: "--processing_mode=V".')
    parser.add_argument('-od', '--onedrive', type=str, help=argparse.SUPPRESS) # simulates the OneDrive root for debugging purposes

def _get_config_arguments(parser: argparse.ArgumentParser):
    group = parser.add_argument_group('configuratie opties')
    group.add_argument('-r', '--root', type=str, 
                        help='De rootdirectory voor het opslaan van nieuwe aanvragen of verslagen.\nAls geen directory wordt ingevoerd (-r=) wordt deze opgevraagd.')
    group.add_argument('-o', '--output', dest='output',  type=str, 
                        help='De directory voor het aanmaken en invullen van beoordelingsformulieren.\nAls geen directory wordt ingevoerd (-o=) wordt deze opgevraagd.')
    group.add_argument('-bb', '--bbinput', dest='bbinput',  type=str, 
                        help='De directory waar Blackboard .ZIP-files (voor invoer verslagen) worden gelezen.\nAls geen directory wordt ingevoerd (-bb=) wordt deze opgevraagd.')
    group.add_argument('-d', '--database', type=str, help='De naam van de databasefile om mee te werken.\nAls de naam niet wordt ingevoerd (-d=) wordt hij opgevraagd.\nIndien de databasefile niet bestaat wordt hij aangemaakt.')   
    group.add_argument('-rf', '--report_file', type=str, help='Bestandsnaam [.xlsx] voor actie "report". default: uit CONFIG.INI')
    group.add_argument('-x', '--excel_in', type=str, help='Bestandsnaam [.xlsx] voor actie "input" vanuit excel-bestand. Moet worden ingevoerd voor deze actie.')
    group.add_argument('-c', '--config', type=str, help='Laad een alternatieve configuratiefile. Aangenomen wordt dat dit een .INI bestand is.')

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

if __name__=="__main__":
    args = _get_arguments()
    print(args)
