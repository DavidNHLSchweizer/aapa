from __future__ import annotations
from typing import Any
from data.storage.general.mappers import ColumnMapper
from data.storage.general.query_builder import QIF
from data.storage.general.storage_const import DBtype, KeyClass, StoredClass
from data.storage.table_registry import CRUD
from database.sql_expr import SQE, Ops
from general.classutil import classname
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

class TableCRUD(CRUD):
    #basic CRUD operations on one table
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
    def create_references(self, aapa_obj: StoredClass):
        for mapper in self.mapper.mappers():
            if isinstance(mapper, CRUDColumnMapper):
                self.ensure_exists(aapa_obj, mapper.attribute_name, mapper.attribute_key)

