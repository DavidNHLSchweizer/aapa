from general.args import AAPAConfigOptions, AAPAProcessingOptions, ArgumentOption, get_options_from_commandline, get_debug
from general.log import init_logging
from general.preview import Preview
from process.aapa_processor.aapa_config import AAPAConfiguration, LOGFILENAME
from process.aapa_processor.aapa_processor import AAPAProcessor, AAPARunnerContext

class AAPARunner:
    def __init__(self, config_options: AAPAConfigOptions):
        self.configuration = AAPAConfiguration(config_options)
        self.initialized = False
    def process(self, processing_options: AAPAProcessingOptions):
        with AAPARunnerContext(self.configuration, processing_options) as context:
            if context is None:
                return
            with Preview(context.needs_preview(), self.configuration.storage, 'main'):
                AAPAProcessor().process(self.configuration, processing_options)
if __name__=='__main__':
    init_logging(LOGFILENAME, get_debug())
    aapa_runner = AAPARunner(get_options_from_commandline(ArgumentOption.CONFIG))
    aapa_runner.process(get_options_from_commandline(ArgumentOption.PROCES)) 
