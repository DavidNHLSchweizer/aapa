from main.args import get_debug
from main.options import AAPAConfigOptions, AAPAProcessingOptions, ArgumentOption, get_options_from_commandline
from main.log import init_logging
from process.general.preview import Preview
from process.main.aapa_config import AAPAConfiguration, LOGFILENAME
from process.main.aapa_processor import AAPAProcessor, AAPARunnerContext

class AAPARunner:
    """ Wrapper object that runs AAPA, ensuring the proper context exists """
    def __init__(self, config_options: AAPAConfigOptions):
        self.configuration = AAPAConfiguration(config_options)
        self.initialized = False
    def process(self, processing_options: AAPAProcessingOptions):
        with AAPARunnerContext(self.configuration, processing_options) as context:
            if context is None:
                print('Fout bij opstarten AAPA.')
                return        
            with Preview(context.needs_preview(), context.storage, 'main'):
                AAPAProcessor().process(self.configuration, processing_options)
if __name__=='__main__':
    init_logging(LOGFILENAME, get_debug())
    aapa_runner = AAPARunner(get_options_from_commandline(ArgumentOption.CONFIG))
    aapa_runner.process(get_options_from_commandline(ArgumentOption.PROCES)) 
