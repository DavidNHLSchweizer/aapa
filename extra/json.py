""" JSON: run encoded JSON file. 
    
    Voert de eerder gegenereerde sql-code uit een gedumpte JSON-file uit in de database.
    Indien -preview wordt de code niet uitgevoerd maar afgedrukt op de console.

    De json-file moet gemaakt zijn met behulp van SQLCollector(s) (module: general.sql_coll)
    
"""
from argparse import ArgumentParser, Namespace
from general.log import init_logging
from general.preview import Preview
from general.sql_coll import import_json
from process.aapa_processor.aapa_processor import AAPARunnerContext

def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--json', dest='json', required=True, type=str,help='JSON filename om uit te voeren.') 
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    json_filename=namespace.json 
    storage = context.configuration.storage
    with Preview(context.processing_options.preview,storage,'Voer JSON SQL-code uit'):
        import_json(storage.database, json_filename, context.processing_options.preview)
    