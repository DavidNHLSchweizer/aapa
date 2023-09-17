from general.args import AAPAoptions, get_arguments, get_debug
from general.log import init_logging, log_error
from general.preview import Preview
from process.aapa_processor.aapa_config import AAPAconfiguration, LOGFILENAME
from process.aapa_processor.aapa_processor import AAPAProcessor, AAPARunnerContext

class AAPARunner:
    def __init__(self, options: AAPAoptions):
        self.configuration = AAPAconfiguration(options)
    def process(self):
        if not self.configuration.initialize():
            log_error(f'{self.configuration.validation_error}\nKan AAPA niet initialiseren.')
            return
        with AAPARunnerContext(self.configuration.options):
            with Preview(self.configuration.preview, self.configuration.storage, 'main'):
                AAPAProcessor().process(self.configuration)

if __name__=='__main__':
    init_logging(LOGFILENAME, get_debug())
    aapa_runner = AAPARunner(get_arguments())
    aapa_runner.process() 
