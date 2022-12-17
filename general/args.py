import argparse
from dataclasses import dataclass

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
    group.add_argument('-init', action='store_true', help= 'Initialiseer de database. Alle data wordt verwijderd.')
    group.add_argument('-x', '--xlsx', type=str, help='Rapporteer aanvragen in een .XSLX bestand. Indien geen bestandsnaam wordt ingevoerd (-x=) gaat alleen een samenvatting naar de console.')
    group.add_argument('-clean',  action='store_true', help='Verwijder overbodige bestanden van verwerkte aanvragen.')
    group.add_argument('-noscan', action='store_true', help='Scan niet op nieuwe aanvragen.')
    group.add_argument('-nomail', action='store_true', help='Beoordeelde bestanden worden niet verwerkt.')
    return parser.parse_args()

@dataclass
class AAPAoptions:
    root: str = None
    forms: str= None
    mail: str= None
    database: str = r'.\aapa.db'
    initialize: bool=False
    report: str = None
    clean: bool = False
    noscan: bool = False
    nomail: bool = False
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
        if self.initialize:
            result = result + f'initialiseer database\n'
        if self.report is not None:
            result = result + f'report: {self.report}\n'
        return result + f'verwijder bestanden: {self.clean}  niet scannen aanvragen: {self.noscan}  niet verwerken beoordeelde formulieren: {self.nomail}.'

def get_arguments()->AAPAoptions:
    args = _get_arguments('Als er geen opties worden gekozen wordt de huidige rootdirectory gescand op nieuwe aanvragen, en worden beoordeelde aanvragen verwerkt.')
    return AAPAoptions(root=args.root, forms=args.forms, mail=args.mail, database=args.database, initialize=args.init, report=args.xlsx, clean=args.clean, noscan=args.noscan, nomail=args.nomail)


if __name__=="__main__":
    options = get_arguments()
    print(options)
