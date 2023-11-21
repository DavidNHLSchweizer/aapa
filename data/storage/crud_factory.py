from typing import Type

from attr import dataclass
from data.classes.aggregator import Aggregator
from data.crud.crud_const import AAPAClass
# from data.crud.crud_base import AAPAClass, StorageCRUD, CRUD_AggregatorData
from data.storage.storage_base import StorageCRUD
from database.database import Database
from database.table_def import TableDefinition
from debug.debug import classname
from general.singleton import Singleton
@dataclass
class CRUD_AggregatorData:
    main_table_key: str # TBD, weet niet meer waar dit voor dient
    aggregator: Aggregator
    attribute: str

# (self, database: Database, class_type: AAPAClass, table: TableDefinition, autoID=False):
class CRUD_factory(Singleton):
    def __init__(self):
        self._registered_CRUDs = {}
    def register(self, class_type: AAPAClass, table: TableDefinition, aggregator_data: CRUD_AggregatorData = None, autoID=False):
        if self._is_registered(class_type):
            raise TypeError(f'Class type {classname(class_type)} already registered.')
        self._registered_CRUDs[class_type] = {'table': table, 'aggregator_data': aggregator_data, 'autoID': autoID}
    def _is_registered(self, class_type: AAPAClass)->bool:
        return class_type in self._registered_CRUDs.keys()
    def create(self, database: Database, class_type: AAPAClass)->StorageCRUD:
        if not self._is_registered(class_type):
            return None
        entry = self._registered_CRUDs[class_type]
        if entry['aggregator_data']:
            return StorageCRUD(database=database, class_type=class_type, table=entry['table'], aggregator_data = entry['aggregator_data'])
        else:
            return StorageCRUD(database=database, class_type=class_type, table=entry['table'], autoID=entry['autoID'])

_crud_factory = CRUD_factory()

def createCRUD(database: Database, class_type: AAPAClass)->StorageCRUD:
    return _crud_factory.create(database, class_type)
def registerCRUD(class_type: AAPAClass, table: TableDefinition=None, aggregator_data: CRUD_AggregatorData = None, autoID=False):
    _crud_factory.register(class_type, table=table, aggregator_data=aggregator_data,  autoID=autoID)