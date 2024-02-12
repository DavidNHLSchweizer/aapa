from __future__ import annotations
import datetime
from pathlib import Path
from typing import Any

from database.aapa_database import create_root
from data.general.aapa_class import AAPAclass
from data.classes.base_dirs import BaseDir
from data.general.detail_rec import DetailRec
from storage.general.CRUDs import CRUD, CRUDQueries, EnsureKeyAction, create_crud, get_registered_type
from storage.general.storage_const import KeyClass, StorageException, StoredClass
from database.classes.database import Database
from data.general.roots import Roots
from general.classutil import classname, find_all_modules
from general.log import log_debug
   
class AAPAStorage: 
    #main interface with the database
    def __init__(self, database: Database):
        self.database: Database = database
        self._crud_dict:dict[str,CRUD] = {}
        self._class_index: dict[AAPAclass,CRUD] = {}
        self.__init_modules()
    def __init_modules(self):
        #initialize the crud variables from the actual modules in the data.storage.classes directory
        #uses some neat tricks with python types, if load_as_well is not set to True the module loading order is 
        #f'ed up and we get unwanted errors. 
        # NOTE: its looks like force-importing the modules takes a relatively long time, 
        # but this can't be helped easily and anyway, they must be loaded at some point
        for full_module_name in find_all_modules("data.storage.classes", True):
            module_name = full_module_name.split(".")[-1]
            if (class_type := get_registered_type(full_module_name)):
                crud = create_crud(self.database, class_type)
                log_debug(f'STORAGE: loaded {module_name} ({classname(class_type)})')
                self._crud_dict[module_name] = crud
                self._class_index[class_type] = crud
    def crud(self, module: str)->CRUD:
        return self._crud_dict.get(module, None)
    def queries(self, module: str)->CRUDQueries:
        if crud := self.crud(module):
            return crud.queries
        raise StorageException(f'{classname(self)}: no Queries for {module}.')

    #----------- queries stuff --------------
    def ensure_key(self, module: str, aapa_obj: StoredClass)->EnsureKeyAction:
        return self.queries(module).ensure_key(aapa_obj)
    def find_max_id(self, module: str)->int:
        return self.queries(module).find_max_id()
    def find_max_value(self, module: str, attribute: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None)->Any:
        return self.queries(module).find_max_value(attribute=attribute, where_attributes=where_attributes, where_values=where_values)
    def find_count(self, module: str, attributes: str|list[str], values: Any|list[Any])->int:
        return self.queries(module).find_count(attributes, values)
    def find_values(self, module: str, attributes: str|list[str], values: Any|list[Any], 
                    map_values = True, read_many=False)->list[AAPAclass]:
        return self.queries(module).find_values(attributes=attributes, values=values, 
                                                map_values = map_values, read_many=read_many)
    def find_all(self, module: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None, map_values=True)->list[Any]:
        if where_attributes:
            if rows := self.queries(module).find_values_where(attribute='id', 
                                                              where_attributes=where_attributes, where_values=where_values):
                return self.read_many(module, {row['id'] for row in rows})
        else:
            return self.queries(module).find_all(map_values)
   
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
    def read_many(self, module: str, keys: set[KeyClass])->StoredClass:
        if crud := self.crud(module):
            return crud.read_many(keys)
        return None
    def update(self, module: str, aapa_obj: StoredClass):
        if crud := self.crud(module):
            crud.update(aapa_obj)
    def delete(self, module: str, aapa_obj: StoredClass):
        if crud := self.crud(module):
            crud.delete(aapa_obj)    
    def add_file_root(self, root: str, code = None)->str:
        encoded_root = Roots.encode_path(root)
        code = Roots.add_root(encoded_root, code)
        if encoded_root != code: 
        #this means the root is already registered, re-encoding causes it to reduce to just the code
            create_root(self.database, code, encoded_root)
            # self.commit()
        return code
    def add_basedir(self, basedir: str|Path, year: int = datetime.datetime.today().year, period: str = '1', forms_version='?'):        
        self.add_file_root(basedir)
        new_basedir = BaseDir(year, period, forms_version, Roots.encode_path(str(basedir)))
        self.queries('base_dirs').ensure_key(new_basedir)
        self.crud('base_dirs').create(new_basedir)
    def commit(self):
        self.database.commit()

        
