from argparse import ArgumentParser, Namespace
from process.aapa_processor.aapa_processor import AAPARunnerContext

EXTRA_DOC = """ documentatie voor de specifieke module. Wordt afgedrukt bij -module_help """

def prog_parser(base_parser: ArgumentParser)->ArgumentParser:
    """
        entry point voor run_extra module-specifieke opties
        voeg hier extra opties toe aan de parser, als nodig. 
        
        voorbeeld:
        base_parser.add_argument('--voorbeeld',type=str, help='Voorbeeld!')
    """
    return base_parser

def extra_action(context:AAPARunnerContext, namespace: Namespace):
    with context:
        """
            entry point voor run_extra 
            voeg hier de uit te voeren code toe
            de AAPA context kan worden gebruikt voor toegang tot storage en opties
            eventuele module-specifieke opties kunnen uit de namespace worden gehaald.
        """
        print('namespace:', namespace)        
        print('configuratie:', context.configuration)
    