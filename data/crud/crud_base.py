from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from data.classes.aggregator import Aggregator
from data.crud.mappers import ColumnMapper, TableMapper#, generate_find_SQL, generate_where_clause_from_object
from data.crud.crud_const import AAPAClass, DBtype, KeyClass
from data.crud.table_search import TableSearcher

from database.dbConst import EMPTY_ID
from database.sql_expr import Ops, SQE
from database.sql_table import SQLselect
from debug.debug import classname
from database.database import Database
from database.table_def import TableDefinition
from general.keys import get_next_key
from general.log import log_debug


@dataclass
class CRUD_AggregatorData:
    main_table_key: CRUDbase
    aggregator: Aggregator
    attribute: str

class CRUD(Enum):
    INIT = auto()
    CREATE=auto()
    READ  =auto()
    UPDATE=auto()
    DELETE=auto()
class CRUD(Enum):
    INIT = auto()
    CREATE=auto()
    READ  =auto()
    UPDATE=auto()
    DELETE=auto()

class CRUDbase:    
    #base class
    def __init__(self, database: Database, class_type: AAPAClass, 
                 table: TableDefinition, no_column_ref_for_key = False, autoID=False):
        self.database = database
        self.no_column_ref_for_key = no_column_ref_for_key
        self.autoID = autoID
        self.aggregator_CRUD_temp: CRUDbase = None
        self.mapper = TableMapper(table, class_type)
        self.customize_mapper()
        self._post_action(None, CRUD.INIT) 
        # can later probably be improved through direct assignment of mapper, now used to adapt column mappers
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    @property
    def class_type(self)->AAPAClass:
        return self.mapper.class_type
    def customize_mapper(self):
        pass #for non-standard column mappers
    def set_mapper(self, column_mapper: ColumnMapper):
        self.mapper.set_mapper(column_mapper)
    def _set_key(self, aapa_obj: AAPAClass):
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
    def create(self, aapa_obj: AAPAClass):
        TS = TableSearcher(self.database, self.mapper)
        log_debug(TS.find_id(aapa_obj))
        log_debug(f'CRUD({classname(self)}) create {str(aapa_obj)}')
        if self.check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
        columns,values = self.mapper.object_to_db(aapa_obj)
        self.database.create_record(self.table, columns=columns, values=values)
        # if self.aggregator_CRUD_temp:
        #     self.aggregator_CRUD_temp.create(aapa_obj)
        self._post_action(aapa_obj, CRUD.CREATE)
    def read(self, key: KeyClass, multiple=False)->AAPAClass|list:
        log_debug(f'CRUD({classname(self)}) read {key}')
        if rows := self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.mapper.value_to_db(key, self.table.key))):
            if multiple:
                return rows #deal with this later!
            else:
                return self.mapper.db_to_object(rows[0])
        return None 
    def update(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD({classname(self)}) update {str(aapa_obj)}')
        columns,values= self.mapper.object_to_db(aapa_obj,include_key=False)
        self.database.update_record(self.table, columns=columns, values=values, 
                                    where=self._generate_where_clause_from_object(aapa_obj, column_names=self.mapper.table_keys()))
        self._post_action(aapa_obj, CRUD.UPDATE)
    def delete(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD({classname(self)}) delete {str(aapa_obj)}')
        self.database.delete_record(self.table, 
                                    where=self._generate_where_clause_from_object(aapa_obj, column_names=self.mapper.table_keys()))
        
    def find_object(self, aapa_obj: AAPAClass)->AAPAClass:
        TS = TableSearcher(self.database, self.mapper)
        return TS.find_id(aapa_obj)
        # if rows := self.database.execute_select(self._generate_find_SQL_from_object(aapa_obj)):
        #     return self.mapper.db_to_object(rows[0])
        return None
    def find_from_values(self, attribute_names: list[str], attribute_values: list[Any])->AAPAClass:
        if rows := self.database.execute_select(self._generate_find_SQL_from_values(attribute_names=attribute_names, attribute_values=attribute_values)):
            return self.mapper.db_to_object(rows[0])
        return None

    def _pre_action(self, aapa_obj: AAPAClass, crud_action: CRUD)->AAPAClass:
        # placeholder for possible preprocessing, may modify object
        pass
    def _post_action(self, aapa_obj: AAPAClass, crud_action: CRUD)->AAPAClass:
        # placeholder for possible postprocessing, may modify object
        return aapa_obj  
    def check_already_there(self, aapa_obj: AAPAClass)->bool:
#todo: move this to storage
        if stored := self.find_object(aapa_obj): #dit gaat niet goed bij aanvragen, wschlijk om de student?
            if stored == aapa_obj:
                log_debug(f'--- already in database ----')                
            else:
                log_debug(f'--- different in database ----')
            #find checks without key, so the key could still be EMPTY_ID, make sure aapa_obj receives this change
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, getattr(stored, self.table.key))
            return True
        return False
    # def _generate_find_SQL_from_object(self, aapa_obj: AAPAClass)->SQLselect:
    #     return generate_find_SQL(self.mapper, aapa_obj, columns=self.mapper.table_keys(), 
    #                              where_attribute_names=self.mapper.attributes(include_key=False), 
    #                              no_column_ref_for_key=self.no_column_ref_for_key)
    # def _generate_find_SQL_from_values(self, attribute_names: list[str], attribute_values: list[Any])->SQLselect:
    #     return generate_find_SQL(self.mapper, attribute_values=attribute_values, where_attribute_names=attribute_names, no_column_ref_for_key=self.no_column_ref_for_key)
    # def _generate_find_SQL(self, column_names: list[str], attribute_names= list[Any])->SQLselect:

    #     attribute_names=self.mapper.table_keys(), 
    #     return generate_find_SQL(self.mapper, where_column_names=column_names, attribute_namesattribute_values=attribute_values, no_column_ref_for_key=self.no_column_ref_for_key)
    def _generate_where_clause_from_object(self, aapa_obj: AAPAClass, column_names: list[str], attribute_names: list[str]=None)->SQE:
        return generate_where_clause_from_object(self.mapper, aapa_obj, column_names=column_names, attribute_names=attribute_names,
                                                                no_column_ref_for_key=self.no_column_ref_for_key)

class CRUDColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str, crud: CRUDbase, attribute_key:str='id'):
        super().__init__(column_name=column_name, attribute_name=attribute_name)
        self.crud = crud
        self.attribute_key = attribute_key
    def map_value_to_db(self, value: AAPAClass)->DBtype:
        return getattr(value, self.attribute_key, None)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return self.crud.read(db_value)