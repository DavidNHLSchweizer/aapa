from __future__ import annotations
import keyword
from typing import Any

from data.aapa_database import create_root
from data.classes.aapa_class import AAPAclass
from data.storage.CRUDs import CRUD, CRUDhelper, create_crud, get_registered_type
from data.storage.general.storage_const import KeyClass, StorageException, StoredClass
from database.database import Database
from data.roots import add_root, encode_path
from general.classutil import find_all_modules
from general.log import log_exception
   
class AAPAStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self._crud_dict:dict[str,CRUD] = {}
        self._class_index: dict[AAPAclass,CRUD] = {}
        self.__init_modules()
    def __init_modules(self):
        #initialize the crud variables from the actual modules in the data.storage.classes directory
        #uses some neat tricks with python types
        for full_module_name in find_all_modules("data.storage.classes", True):
            module_name = full_module_name.split(".")[-1]
            if (class_type := get_registered_type(full_module_name)):
                crud = create_crud(self.database, class_type)
                self._crud_dict[module_name] = crud
                self._class_index[class_type] = crud
    def crud(self, attribute: str)->CRUD:
        return self._crud_dict.get(attribute, None)
    def helper(self, attribute: str)->CRUDhelper:
        if crud := self.crud(attribute):
            return crud.helper
        return None
    def call_helper(self, _module: str, helper_function: str, **kwdargs)->Any:
        if (helper := self.helper(_module)):
            return getattr(helper,helper_function)(**kwdargs)
        raise StorageException(f'Can not call helper {_module} {helper_function}  ({kwdargs})')
    def create(self, aapa_obj: StoredClass):
        if crud := self.__find_crud(aapa_obj):
            crud.create(aapa_obj)
    def read(self, attribute: str, key: KeyClass|list[KeyClass])->StoredClass:
        if crud := self.crud(attribute):
            return crud.read(key)
        return None
    def update(self, aapa_obj: StoredClass):
        if crud := self.__find_crud(aapa_obj):
            crud.update(aapa_obj)
    def delete(self, aapa_obj: StoredClass):
        if crud := self.__find_crud(aapa_obj):
            crud.delete(aapa_obj)
    def __find_crud(self, aapa_obj: StoredClass)->CRUD:
        return self._class_index.get(type(aapa_obj), None)
    def add_file_root(self, root: str, code = None)->str:
        encoded_root = encode_path(root)
        code = add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduce to just the code
            create_root(self.database, code, encoded_root)
            self.commit()
    def commit(self):
        self.database.commit()