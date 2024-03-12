import inspect
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.general.const import MijlpaalType
from data.classes.files import File
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from tests.random_data import RandomData

def find_aggregator(object: AAPAclass)->tuple[str,Aggregator]:
    for name,value in inspect.getmembers(object):
        if name[0] != '_' and issubclass(type(value),Aggregator): 
            return(name, value)

def find_aggregator2(object: AAPAclass)->tuple[str,Aggregator]:
    for name,value in inspect.getmembers_static(object, inspect.isclass):
        print(name, value)

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True


    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        aanvraag = self.storage.read('aanvragen', 98)
        print(aanvraag)
        for file in aanvraag.files_list:
            print(file)
        return True
    