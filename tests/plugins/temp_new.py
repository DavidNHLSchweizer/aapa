from data.general.const import MijlpaalType
from data.classes.files import File
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from tests.random_data import RandomData

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True

    
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        RD = RandomData(self.storage)
        self.test_aanvragen(RD)
        self.test_undologs(RD)
        self.database.commit()
        return True
    