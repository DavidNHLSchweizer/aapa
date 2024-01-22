
from general.args import get_options_from_commandline
from migrate.remover import AanvraagRemover
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.aapa_processor.aapa_processor import AAPARunnerContext

if __name__ == "__main__":
    (config_options, processing_options, other_options) = get_options_from_commandline()
    with AAPARunnerContext(AAPAConfiguration(config_options), processing_options, other_options) as context:
        storage = context.configuration.storage
        remover = AanvraagRemover(storage)
        remover.remove([205], processing_options.preview)
