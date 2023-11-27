from __future__ import annotations
from dataclasses import dataclass
from typing import Type
from data.classes.aggregator import Aggregator
from data.storage.mappers import TableMapper
from data.storage.storage_const import StoredClass, DetailRec
from database.table_def import TableDefinition
from debug.debug import classname
from general.singleton import Singleton

class TableRegistryException(Exception): pass
@dataclass
class ClassRegistryData:
    table: TableDefinition
    mapper_type: Type[TableMapper] # to use custom mappers
    autoID: bool
    aggregator_data: ClassAggregatorData 

@dataclass
class ClassAggregatorData:
    attribute: str
    class_type: Type[StoredClass]

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
    def register(self, class_type:StoredClass, table: TableDefinition, mapper_type: type[TableMapper], aggregator_data: ClassAggregatorData = None, autoID=False):
        self.__check_valid(class_type, False)
        self._registered_data[class_type] = ClassRegistryData(table=table, autoID=autoID,                                                                mapper_type = mapper_type, aggregator_data=aggregator_data)
    def _is_registered(self, class_type: StoredClass)->bool:
        return class_type in self._registered_data.keys()
    def class_data(self, class_type: StoredClass)->ClassRegistryData:
        self.__check_valid(class_type, True)      
        return self._registered_data[class_type]
        # if entry['aggregator_data']:
        #     return StorageCRUD(database=database, class_type=class_type, table=entry['table'], aggregator_data = entry['aggregator_data'])
        # else:
        #     return StorageCRUD(database=database, class_type=class_type, table=entry['table'], autoID=entry['autoID'])
    # def cl
    # def class_table(self, class_type: AAPAclass|DetailRec)->TableDefinition:
    #     if not self._is_registered(class_type):
    #         return None        
    #     return self._registered_CRUDs[class_type]['table']

_table_registry = TableRegistry()

def class_data(class_type: Type[StoredClass])->ClassRegistryData:
    return _table_registry.class_data(class_type)
def register_table(class_type: Type[StoredClass], table: TableDefinition=None, 
                   mapper_type: Type[TableMapper] = None, 
                   aggregator_data: ClassAggregatorData = None, autoID=False):
    _table_registry.register(class_type, table=table, mapper_type=mapper_type, aggregator_data=aggregator_data,  autoID=autoID)