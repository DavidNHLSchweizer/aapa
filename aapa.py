from general.args import AAPAoptions, get_arguments
from general.config import config
from general.log import init_logging
from general.preview import Preview
from process.aapa_processor.aapa_config import AAPAconfiguration, LOGFILENAME
from process.aapa_processor.aapa_processor import AAPAProcessor, AAPARunnerContext

class AAPARunner:
    def __init__(self, options: AAPAoptions):
        self.configuration = AAPAconfiguration(options)
    def process(self):
        self.configuration.initialize()        
        with AAPARunnerContext(self.configuration.options):
            with Preview(self.configuration.preview, self.configuration.storage, 'main'):
                AAPAProcessor().process(self.configuration)

if __name__=='__main__':
    init_logging(LOGFILENAME)
    aapa_runner = AAPARunner(get_arguments())
    aapa_runner.process() 
