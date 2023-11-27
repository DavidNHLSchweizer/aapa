from __future__ import annotations
from dataclasses import dataclass
from typing import Type
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRecData
from data.storage.mappers import TableMapper
from data.storage.storage_const import StoredClass, DetailRec
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
    def register(self, class_type:StoredClass, table: TableDefinition, mapper_type: type[TableMapper], 
                 details_data: DetailRecData = None, autoID=False):
        self.__check_valid(class_type, False)
        self._registered_data[class_type] = ClassRegistryData(table=table, autoID=autoID,                                                                
                                                              mapper_type = mapper_type, details_data=details_data)
    def _is_registered(self, class_type: StoredClass)->bool:
        return class_type in self._registered_data.keys()
    def class_data(self, class_type: StoredClass)->ClassRegistryData:
        self.__check_valid(class_type, True)      
        return self._registered_data[class_type]

_table_registry = TableRegistry()

def class_data(class_type: Type[StoredClass])->ClassRegistryData:
    return _table_registry.class_data(class_type)
def register_table(class_type: Type[StoredClass], table: TableDefinition=None, 
                   mapper_type: Type[TableMapper] = None, 
                   details_data: DetailRecData = None, autoID=False):
    _table_registry.register(class_type, table=table, mapper_type=mapper_type,
                              details_data=details_data,  autoID=autoID)