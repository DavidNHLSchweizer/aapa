from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Type
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRecData
from data.storage.general.mappers import TableMapper
from data.storage.general.query_builder import QueryBuilder
from data.storage.general.storage_const import KeyClass, StoredClass
from database.database import Database
from database.dbConst import EMPTY_ID
from database.table_def import TableDefinition
from general.classutil import classname
from general.keys import get_next_key
from general.log import log_debug
from general.singleton import Singleton

class TableRegistryException(Exception): pass
@dataclass
class ClassRegistryData:
    table: TableDefinition
    mapper_type: Type[TableMapper] # to use custom mappers
    autoID: bool
    details_data: DetailRecData 
    crud: Type[CRUD]

class CRUDs(dict):
    # utility class to access one or more associated cruds
    # any cruds are created as needed 
    # (for e.g. associated class types such as Milestone.student, or detail tables)
    def __init__(self, database: Database):
        self.database=database
    def get_crud(self, class_type: StoredClass)->CRUD:
        if not (crud := self.get(class_type, None)):
            crud = create_crud(self.database, class_type)
        self[class_type] = crud
        return crud

class CRUD:
    def __init__(self, database: Database, class_type: StoredClass):
        self.data = _class_data(class_type)
        self.database = database        
        self.autoID = self.data.autoID
        self.mapper = self.data.mapper_type(database, self.data.table, class_type) if self.data.mapper_type \
                                                            else TableMapper(database, self.data.table, class_type)
        self.query_builder = QueryBuilder(self.database, self.mapper)
        self._cruds = CRUDs(database)
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    @property
    def class_type(self)->StoredClass:
        return self.mapper.class_type   
    def get_crud(self, class_type)->CRUD:
        return self if class_type == self.class_type else self._cruds.get_crud(class_type)
    @abstractmethod
    def create(self, aapa_obj: StoredClass): pass
    @abstractmethod
    def read(self, key: KeyClass|list[KeyClass])->StoredClass: pass
    @abstractmethod
    def update(self, aapa_obj: StoredClass): pass
    @abstractmethod
    def delete(self, aapa_obj: StoredClass): pass
    #utility functions
    def _check_already_there(self, aapa_obj: StoredClass)->bool:
        if stored_ids := self.query_builder.find_id_from_object(aapa_obj): 
            log_debug(f'--- already in database ----')                
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, stored_ids[0])
            return True
        return False
    def _create_key_if_needed(self, aapa_obj: StoredClass, table: TableDefinition = None, autoID=True):
        autoID = autoID if autoID else self.autoID
        table = table if table else self.table
        if autoID and getattr(aapa_obj, table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, table.key, get_next_key(table.name))
    def ensure_key(self, aapa_obj: StoredClass):
        if not self._check_already_there(aapa_obj):
            self._create_key_if_needed(aapa_obj)
    def ensure_exists(self, aapa_obj: StoredClass, attribute: str, attribute_key: str = 'id'):
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            return
        crud = self.get_crud(type(attr_obj))
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_ids := crud.query_builder.find_id_from_object(attr_obj):
                setattr(attr_obj, attribute_key, stored_ids[0])
            else:
                self._create_key_if_needed(attr_obj, crud.table, crud.autoID)
                crud.create(attr_obj)
        else:
            # key already set elsewhere, check whether already in database
            if not (stored_ids := crud.query_builder.find_id_from_object(attr_obj)):
                crud.create(attr_obj)




# (self, database: Database, class_type: AAPAClass, table: TableDefinition, autoID=False):
class TableRegistry(Singleton):
    def __init__(self):
        self._registered_data = {}
    def __check_valid(self, class_type: StoredClass, expect_registered=False)->None:
        if isinstance(class_type, StoredClass):
            raise TableRegistryException(f'{class_type} is an instance. Only types can be registered.')
        if not issubclass(class_type, StoredClass):
            raise TableRegistryException(f'Unexpected {class_type} can not be registered.')
        if not expect_registered and self._is_registered(class_type):
            raise TableRegistryException(f'Class type {classname(class_type)} already registered.')
        elif expect_registered and not self._is_registered(class_type):
            raise TableRegistryException(f'Class type {class_type} is not registered.')        
    def register(self, class_type:StoredClass, crud:CRUD, table: TableDefinition, mapper_type: type[TableMapper], 
                 details_data: DetailRecData = None, autoID=False):
        self.__check_valid(class_type, False)
        self._registered_data[class_type] = ClassRegistryData(table=table, crud=crud, autoID=autoID,                                                                
                                                              mapper_type = mapper_type, details_data=details_data)
    def _is_registered(self, class_type: StoredClass)->bool:
        return class_type in self._registered_data.keys()
    def class_data(self, class_type: StoredClass)->ClassRegistryData:
        self.__check_valid(class_type, True)      
        return self._registered_data[class_type]

_table_registry = TableRegistry()


def create_crud(database: Database, class_type: StoredClass)->CRUD:
    return _class_data(class_type).crud(database, class_type)

def _class_data(class_type: Type[StoredClass])->ClassRegistryData:
    return _table_registry.class_data(class_type)
def register_table(class_type: Type[StoredClass], crud: CRUD, table: TableDefinition=None, 
                   mapper_type: Type[TableMapper] = None, 
                   details_data: DetailRecData = None, autoID=False):
    _table_registry.register(class_type, crud=crud, table=table, mapper_type=mapper_type,
                              details_data=details_data,  autoID=autoID)
    