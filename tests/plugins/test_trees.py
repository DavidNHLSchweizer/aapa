
from data.classes.aanvragen import Aanvraag
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from data.general.const import MijlpaalType
from data.classes.files import File
# from data.general.trees import TreeBuilder
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from tests.random_data import RandomData
from PrettyPrint import PrettyPrintTree

class AAPATree:
    def __init__(self):
        self.print_tree = PrettyPrintTree(self.get_children, self.get_value, trim=64, orientation=PrettyPrintTree.Horizontal)
    def get_children(self, node: object)->list[object]:
        if isinstance(node, MijlpaalDirectory):
            return node.mijlpalen
        elif isinstance(node, Aanvraag|Verslag):
            return node.files_list
        elif isinstance(node,File):
            return None
    def get_value(self, node: object)->str:
        if isinstance(node, MijlpaalDirectory):
            return f'{node.id}:{File.display_file(node.directory)}'
        elif isinstance(node, Aanvraag|Verslag):
            return f'{node.id}:{node.summary()}'
        elif isinstance(node, File):
            return f'{node.id}:{File.display_file(node.filename)}'
    def print(self, node: object):
        self.print_tree(node)
    
class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        

        tree1 = AAPATree()
        tree1.print(self.storage.read('aanvragen', 144))
        print()
        tree1.print(self.storage.read('verslagen', 114))

        print()
        tree1.print(self.storage.read('mijlpaal_directories', 114))

        print()


        return True
    