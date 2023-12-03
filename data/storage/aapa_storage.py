from __future__ import annotations
from abc import abstractmethod
import keyword
from typing import Any

from data.aapa_database import create_root
from data.classes.aanvragen import Aanvraag
from data.classes.aapa_class import AAPAclass
from data.storage.CRUDs import CRUD, CRUDQueries, EnsureKeyAction, create_crud, get_registered_type
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
    def crud(self, module: str)->CRUD:
        return self._crud_dict.get(module, None)
    def queries(self, module: str)->CRUDQueries:
        if crud := self.crud(module):
            return crud.queries
        raise StorageException(f'no Queries for {module}.')

    #----------- helper stuff --------------
    def ensure_key(self, module: str, aapa_obj: StoredClass)->EnsureKeyAction:
        return self.queries(module).ensure_key(aapa_obj)
    def find_max_id(self, module: str)->int:
        return self.queries(module).find_max_id()
    def find_max_value(self, module: str, attribute: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None)->Any:
        return self.queries(module).find_max_value(attribute=attribute, where_attributes=where_attributes, where_values=where_values)
    def find_count(self, module: str, attributes: str|list[str], values: Any|list[Any])->int:
        return self.queries(module).find_count(attributes, values)
    def find_values(self, module: str, attributes: str|list[str], values: Any|list[Any], map_values = True)->list[AAPAclass]:
        return self.queries(module).find_values(attributes=attributes, values=values, map_values = map_values)
    def find_all(self, module: str, where_attributes: str|list[str], where_values: Any|list[Any])->list[Any]:
        if rows := self.queries(module).find_values_where(attribute='id', where_attributes=where_attributes, where_values=where_values):
            return [self.read(module, row['id']) for row in rows]
    
    #------------- crud stuff --------------
    def create(self, module: str, aapa_obj: StoredClass):
        if crud := self.crud(module):
            match crud.queries.ensure_key(aapa_obj):
                case EnsureKeyAction.ALREADY_THERE:
                    #note: this could still have set the key for the object
                    return
                case EnsureKeyAction.KEY_CREATED: 
                    crud.create(aapa_obj)
                case _: pass
    def read(self, module: str, key: KeyClass|list[KeyClass])->StoredClass:
        if crud := self.crud(module):
            return crud.read(key)
        return None
    def update(self, module: str, aapa_obj: StoredClass):
        if crud := self.crud(module):
            crud.update(aapa_obj)
    def delete(self, module: str, aapa_obj: StoredClass):
        if crud := self.crud(module):
            crud.delete(aapa_obj)

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
        self.helper = storage.queries(module)
        
