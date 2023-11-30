from __future__ import annotations

from data.aapa_database import create_root
from data.storage.CRUDs import CRUDs, get_registered_type

from database.database import Database
from data.roots import add_root, encode_path
from general.classutil import find_all_modules
   
class AAPAStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self._cruds  = CRUDs(database)
        self.__init_modules()
    def __init_modules(self):
        #initialize the crud variables from the actual modules in the data.storage.classes directory
        #uses some neat tricks with python types
        for full_module_name in find_all_modules("data.storage.classes", True):
            module_name = full_module_name.split(".")[-1]
            if (class_type := get_registered_type(full_module_name)):
                setattr(self,module_name, self._cruds.get_crud(class_type))
    def add_file_root(self, root: str, code = None)->str:
        encoded_root = encode_path(root)
        code = add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduce to just the code
            create_root(self.database, code, encoded_root)
            self.commit()
    def commit(self):
        self.database.commit()