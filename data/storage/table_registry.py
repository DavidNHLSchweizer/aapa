from __future__ import annotations
from dataclasses import dataclass
from data.classes.aggregator import Aggregator
from data.storage.storage_const import AAPAClass
from database.table_def import TableDefinition
from debug.debug import classname
from general.singleton import Singleton

@dataclass
class ClassRegistryData:
    table: TableDefinition
    autoID: bool
    aggregator_data: CRUD_AggregatorData 

@dataclass
class CRUD_AggregatorData:
    main_table_key: str # TBD, weet niet meer waar dit voor dient
    aggregator: Aggregator
    attribute: str

# (self, database: Database, class_type: AAPAClass, table: TableDefinition, autoID=False):
class TableRegistry(Singleton):
    def __init__(self):
        self._registered_CRUDs = {}
    def register(self, class_type: AAPAClass, table: TableDefinition, aggregator_data: CRUD_AggregatorData = None, autoID=False):
        if self._is_registered(class_type):
            raise TypeError(f'Class type {classname(class_type)} already registered.')
        self._registered_CRUDs[class_type] = ClassRegistryData(table=table, autoID=autoID, aggregator_data=aggregator_data)
    def _is_registered(self, class_type: AAPAClass)->bool:
        return class_type in self._registered_CRUDs.keys()
    def class_data(self, class_type: AAPAClass)->ClassRegistryData:
        if not self._is_registered(class_type):
            cn  = classname(class_type)
            raise TypeError(f'Class type {class_type} is not registered.')
        return self._registered_CRUDs[class_type]
        # if entry['aggregator_data']:
        #     return StorageCRUD(database=database, class_type=class_type, table=entry['table'], aggregator_data = entry['aggregator_data'])
        # else:
        #     return StorageCRUD(database=database, class_type=class_type, table=entry['table'], autoID=entry['autoID'])
    # def cl
    # def class_table(self, class_type: AAPAClass)->TableDefinition:
    #     if not self._is_registered(class_type):
    #         return None        
    #     return self._registered_CRUDs[class_type]['table']

_table_registry = TableRegistry()

# def create_CRUD(database: Database, class_type: AAPAClass)->StorageCRUD:
#     return _table_registry.create_CRUD(database, class_type)
def class_data(class_type: AAPAClass)->ClassRegistryData:
    return _table_registry.class_data(class_type)
def register_table(class_type: AAPAClass, table: TableDefinition=None, aggregator_data: CRUD_AggregatorData = None, autoID=False):
    _table_registry.register(class_type, table=table, aggregator_data=aggregator_data,  autoID=autoID)