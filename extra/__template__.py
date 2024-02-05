""" documentatie voor de specifieke module. 

    Zet hier de tekst die wordt afgedrukt bij -module_help 
    
"""

from argparse import ArgumentParser, Namespace
from process.aapa_processor.aapa_processor import AAPARunnerContext

def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    """
        entry point voor run_extra module-specifieke opties
        voeg hier extra opties toe aan de parser, als nodig. 
        
        voorbeeld:
        base_parser.add_argument('--voorbeeld',type=str, help='Voorbeeld!')
    """
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    """
        entry point voor run_extra 
        voeg hier de uit te voeren code toe

        de AAPA context geeft toegang tot storage en opties 
        de context manager wordt al opgestart.
        logging gaat naar "module_name".log

        eventuele module-specifieke opties kunnen uit de namespace worden gehaald.
    """
    print('namespace:', namespace)        
    print('configuratie:', context.configuration)
    