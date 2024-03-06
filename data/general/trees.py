from PrettyPrint import PrettyPrintTree
from data.classes.aanvragen import Aanvraag
from data.classes.files import File

class TreeBuilder:
    def __init__(self, root_name: str):
        self.tree = Tree()
        self.root = self.tree.create_node(root_name)
    def build_aanvraag_node(self, aanvraag: Aanvraag, parent: Node=None)->Node:
        node = self.tree.create_node(aanvraag.summary(), aanvraag.id, parent=self.root if not parent else parent, data=aanvraag)
        # for file in aanvraag.files_list:
        #     tree.create_node(File.display_file(file.filename), file.id, parent=node, data=file)
        return node



