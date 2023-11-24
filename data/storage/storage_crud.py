from data.storage.mappers import TableMapper
from data.storage.query_builder import QueryBuilder
from data.storage.table_registry import class_data
from data.storage.storage_const import AAPAClass, KeyClass
from database.database import Database
from database.dbConst import EMPTY_ID
from database.sql_expr import SQE, Ops
from database.table_def import TableDefinition
from debug.debug import classname
from general.keys import get_next_key
from general.log import log_debug

class StorageCRUD:
    def __init__(self, database: Database, class_type: AAPAClass):
        data = class_data(class_type)
        self.database = database        
        self.autoID = data.autoID
        self.aggregator_data = data.aggregator_data
        self.mapper = data.mapper_type(database, data.table, class_type) if data.mapper_type else TableMapper(database, data.table, class_type)
        self.query_builder = QueryBuilder(self.database, self.mapper)
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    @property
    def class_type(self)->AAPAClass:
        return self.mapper.class_type
    def _create_key_if_needed(self, aapa_obj: AAPAClass):
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
    def create(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD CREATE ({classname(self)}) {str(aapa_obj)}')
        columns,values = self.mapper.object_to_db(aapa_obj)
        self.database.create_record(self.table, columns=columns, values=values)
    def read(self, key: KeyClass, multiple=False)->AAPAClass|list:
        log_debug(f'CRUD READ ({classname(self)}) {key}')
        if rows := self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.mapper.value_to_db(key, self.table.key))):
            if multiple:
                return rows #deal with this later!
            else:
                return self.mapper.db_to_object(rows[0])
        return None 
    def update(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD UPDATE ({classname(self)}) {str(aapa_obj)}')
        columns,values= self.mapper.object_to_db(aapa_obj,include_key=False)
        self.database.update_record(self.table, columns=columns, values=values, 
                                            where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))
    def delete(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD DELETE ({classname(self)}) {str(aapa_obj)}')
        self.database.delete_record(self.table, 
                                    where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))        

# def create_CRUD(self, database: Database, class_type: AAPAClass)->StorageCRUD:
    
#     if not self._is_registered(class_type):
#         return None
#     entry = self._registered_CRUDs[class_type]
#     if entry['aggregator_data']:
#         return StorageCRUD(database=database, class_type=class_type, table=entry['table'], aggregator_data = entry['aggregator_data'])
#     else:
#         return StorageCRUD(database=database, class_type=class_type, table=entry['table'], autoID=entry['autoID'])
