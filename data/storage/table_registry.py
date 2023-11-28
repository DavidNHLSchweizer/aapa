from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Type
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRecData
from data.storage.mappers import TableMapper
from data.storage.query_builder import QueryBuilder
from data.storage.storage_const import KeyClass, StoredClass, DetailRec
from database.database import Database
from database.table_def import TableDefinition
from general.classutil import classname
from general.singleton import Singleton

class TableRegistryException(Exception): pass
@dataclass
class ClassRegistryData:
    table: TableDefinition
    mapper_type: Type[TableMapper] # to use custom mappers
    autoID: bool
    details_data: DetailRecData 
    crud: Type[CRUD]

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
        self.data = class_data(class_type)
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

def create_crud(database: Database, class_type: StoredClass)->CRUD:
    return class_data(class_type).crud(database, class_type
                                       )
def class_data(class_type: Type[StoredClass])->ClassRegistryData:
    return _table_registry.class_data(class_type)
def register_table(class_type: Type[StoredClass], crud: CRUD, table: TableDefinition=None, 
                   mapper_type: Type[TableMapper] = None, 
                   details_data: DetailRecData = None, autoID=False):
    _table_registry.register(class_type, crud=crud, table=table, mapper_type=mapper_type,
                              details_data=details_data,  autoID=autoID)
    