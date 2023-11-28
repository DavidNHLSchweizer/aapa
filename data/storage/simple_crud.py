from __future__ import annotations
from typing import Any
from data.storage.CRUDbase import CRUD
from data.storage.mappers import ColumnMapper
from data.storage.query_builder import QIF
from data.storage.storage_const import DBtype, StoredClass, KeyClass
from database.database import Database
from database.dbConst import EMPTY_ID
from database.sql_expr import SQE, Ops
from general.classutil import classname
from general.keys import get_next_key
from general.log import log_debug

class CRUDColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str, crud: CRUD, attribute_key:str='id'):
        super().__init__(column_name=column_name, attribute_name=attribute_name)
        self.crud = crud
        self.attribute_key = attribute_key
    def map_value_to_db(self, value: StoredClass)->DBtype:
        return getattr(value, self.attribute_key, None)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return self.crud.read(db_value)

class SimpleCRUD(CRUD):
    #basic CRUD operations on one table
    def _check_already_there(self, aapa_obj: StoredClass)->bool:
        if stored_ids := self.query_builder.find_id_from_object(aapa_obj): 
            log_debug(f'--- already in database ----')                
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, stored_ids[0])
            return True
        return False
    def _create_key_if_needed(self, aapa_obj: StoredClass):
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
    def ensure_key(self, aapa_obj: StoredClass):
        if not self._check_already_there(aapa_obj):
            self._create_key_if_needed(aapa_obj)
        self.database.commit()
    def create(self, aapa_obj: StoredClass):
        log_debug(f'CRUD CREATE ({classname(self)}) {classname(aapa_obj)}: {str(aapa_obj)}')
        columns,values = self.mapper.object_to_db(aapa_obj)
        self.database.create_record(self.table, columns=columns, values=values)
        log_debug(f'END CRUD CREATE')
    def read(self, key: KeyClass|list[KeyClass])->StoredClass|list:
        log_debug(f'CRUD READ ({classname(self)}|{self.table.name}) {classname(self.class_type)}:{key=}')
        result = None
        if isinstance(key,list):
            where = self.query_builder.build_where_from_values(column_names=self.table.keys, 
                                                               values=key,flags={QIF.NO_MAP_VALUES})
        else:
            where = SQE(self.table.key, Ops.EQ, self.mapper.value_to_db(key, self.table.key))
        if rows := self.database.read_record(self.table, where=where):
            result = self.mapper.db_to_object(rows[0])
        log_debug(f'END CRUD READ: {str(result)}')
        return result
    def update(self, aapa_obj: StoredClass):
        log_debug(f'CRUD UPDATE ({classname(self)}|{self.table.name}) {classname(aapa_obj)}: {str(aapa_obj)}')
        columns,values= self.mapper.object_to_db(aapa_obj,include_key=False)
        self.database.update_record(self.table, columns=columns, values=values, 
                                            where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))
        log_debug(f'END CRUD UPDATE')
    def delete(self, aapa_obj: StoredClass):
        log_debug(f'CRUD DELETE ({classname(self)}|{self.table.name}) {classname(aapa_obj)}: {str(aapa_obj)}')
        self.database.delete_record(self.table, 
                                    where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))        
        log_debug(f'END CRUD DELETE')

