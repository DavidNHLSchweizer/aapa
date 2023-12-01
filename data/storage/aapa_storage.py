from __future__ import annotations
from abc import abstractmethod
import keyword
from typing import Any

from data.aapa_database import create_root
from data.classes.aanvragen import Aanvraag
from data.classes.aapa_class import AAPAclass
from data.storage.CRUDs import CRUD, CRUDhelper, create_crud, get_registered_type
from data.storage.general.storage_const import KeyClass, StorageException, StoredClass
from database.database import Database
from data.roots import add_root, encode_path
from database.sql_expr import SQE
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
        raise StorageException(f'no helper for {attribute}.')

    #----------- helper stuff --------------
    def ensure_key(self, module: str, aapa_obj: StoredClass):
        self.helper(module).ensure_key(aapa_obj)
    def find_max_value(self, module: str, attribute: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None)->Any:
        return self.helper(module).find_max_value(attribute=attribute, where_attributes=where_attributes, where_values=where_values)
    def find_count(self, module: str, attributes: str|list[str], values: Any|list[Any])->int:
        return self.helper(module).find_count(attributes, values)
    def find_values(self, module: str, attributes: str|list[str], values: Any|list[Any])->list[AAPAclass]:
        return self.helper(module).find_values(attributes=attributes, values=values)
    def find_all(self, module: str, where_attributes: str|list[str], where_values: Any|list[Any])->list[Any]:
        return self.helper(module).find_values_where(attribute='id', where_attributes=where_attributes, where_values=where_values)
    
    #------------- crud stuff --------------
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


class StorageExtension:
    # to define more complicated queries
    def __init__(self, storage: AAPAStorage, module: str):            
        self.storage = storage
        self.module = module
        self.helper = storage.helper(module)
        
