""" JSON: run encoded JSON file. 
    
    Voert de eerder gegenereerde sql-code uit een gedumpte JSON-file uit in de database.
    Indien -preview wordt de code niet uitgevoerd maar afgedrukt op de console.

    De json-file moet gemaakt zijn met behulp van SQLCollector(s) (module: general.sql_coll)
    
"""
from argparse import ArgumentParser
from general.log import log_error, log_print
from general.sql_coll import import_json
from plugins.plugin import PluginBase
from process.aapa_processor.aapa_processor import AAPARunnerContext

class JSONprocessor(PluginBase):
    def get_parser(self) -> ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', type=str,help='JSON filename om uit te voeren.') 
        return parser
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        json_filename=kwdargs.get('json', None)
        if not json_filename:
            log_error('Optie --json is verplicht. Geen JSON-file opgegeven.')
            return False
        storage = context.configuration.storage
        import_json(storage.database, json_filename, context.processing_options.preview)
        log_print(f'JSON file {json_filename} uitgevoerd (preview: {context.processing_options.preview})')
        return True
    