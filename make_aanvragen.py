
from general.args import get_options_from_commandline
from general.log import init_logging
from general.preview import Preview
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.aapa_processor.aapa_processor import AAPARunnerContext
from process.migrate.make_aanvragen import create_aanvragen

if __name__ == "__main__":
    (config_options, processing_options, other_options) = get_options_from_commandline()
    processing_options.debug = True
    processing_options.preview = True
    init_logging('makkie.log', True)
    with AAPARunnerContext(AAPAConfiguration(config_options), processing_options, other_options) as context:        
        storage = context.configuration.storage
        with Preview(True,storage,'Maak extra aanvragen (voor migratie)'):
            create_aanvragen(storage,r'.\migrate\m122')