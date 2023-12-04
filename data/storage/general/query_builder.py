from __future__ import annotations
from enum import Enum
from typing import Any
from data.storage.general.mappers import MapperException, TableMapper
from data.storage.general.storage_const import StoredClass
from database.database import Database
from database.sql_expr import SQE, Ops
from database.sql_table import SQLselect
from general.classutil import classname
from general.log import log_debug

class QueryInfo:
    class Flags(Enum):
        NOFLAGS          = 0 # simple way to signal no flag at all
        INCLUDE_KEY      = 1 # include key in queries 
        NO_MAP_VALUES    = 2 # do not map values for database
        ATTRIBUTES       = 3 # given column names are attributes   
    @staticmethod
    def include_key(flags)->bool:
        return QueryInfo.Flags.INCLUDE_KEY in flags
    @staticmethod
    def no_map_values(flags)->bool:
        return QueryInfo.Flags.NO_MAP_VALUES in flags
    @staticmethod
    def attributes(flags)->bool:
        return QueryInfo.Flags.ATTRIBUTES in flags
    def __init__(self,  mapper: TableMapper):
        self.mapper = mapper
    def __get_columns(self, columns: list[str] = [], flags = {Flags.INCLUDE_KEY, Flags.NO_MAP_VALUES}):
        if QueryInfo.attributes(flags):
            if columns: 
                return self.mapper._get_columns_from_attributes(columns)
            else:
                raise MapperException(f'Invalid combination: no attribute names with flag ATTRIBUTES') 
        else:
            return columns if columns else self.mapper.columns(QueryInfo.include_key)
    def __get_values(self, data_columns: list[str], aapa_obj: StoredClass, values: list[Any], no_map_values: bool)->list[Any]:
        if values:
            if len(values) != len(data_columns):
                log_debug(f'values: {values}  columns: {data_columns}')
                raise MapperException(f'Invalid parameters: {len(values)} values, but {len(data_columns)} columns')              
            if no_map_values:
                data_values = values
            else:
                data_values = [self.mapper._mappers[column_name].map_value_to_db(value)  
                                    for column_name,value in zip(data_columns, values)]
        else: # get values from object
            if not aapa_obj:
                raise MapperException(f'Invalid parameters: provide either an object or values.')
            data_values = []
            for column_name in data_columns:
                mapper = self.mapper._mappers[column_name]
                value = getattr(aapa_obj, mapper.attribute_name)
                data_values.append(value if no_map_values else mapper.map_value_to_db(value))
        return data_values
    def get_data(self, aapa_obj: StoredClass = None, columns: list[str] = [], values: list[Any] = [], 
                 flags = {Flags.INCLUDE_KEY, Flags.NO_MAP_VALUES})->tuple[list[str], list[Any]]:
        data_columns = self.__get_columns(columns, flags)
        data_values = self.__get_values(aapa_obj=aapa_obj, data_columns=data_columns, values=values, no_map_values=QueryInfo.no_map_values(flags)) 
        return (data_columns, data_values)
QIF = QueryInfo.Flags

class QueryBuilder:
    def __init__(self, database: Database, mapper: TableMapper):
        self.database = database
        self.mapper = mapper
        self.query_info = QueryInfo(mapper)
    def __db_log(self, function: str, params: str=''):
        log_debug(f'QB{classname(self.mapper.class_type)}: {function}{(" - " + params) if params else ""}')
    def find_all(self, columns: list[str], where: SQE)->list[Any]:
        self.__db_log('FIND_ALL', f'columns:{columns} where:{where.db_str() if where else None}')
        sql = SQLselect(self.mapper.table, columns=columns, where=where)
        return self.database.execute_select(sql) 
    def find_count(self, where:SQE=None)->int:
        self.__db_log('FIND_COUNT', f'where:{where.db_str() if where else None}')
        sql = SQLselect(self.mapper.table, columns=['count(id)'], where=where)
        if (row := self.database.execute_select(sql)) and row[0][0]:
            return row[0][0]
        return 0
    def find_ids(self):
        self.__db_log('FIND_IDS')
        return self.__find_ids()
    def find_ids_from_object(self, aapa_obj: StoredClass, attributes: list[str] = None, flags={QIF.ATTRIBUTES})->list[int]:
        self.__db_log('FIND_IDS_FROM_OBJECT', f'object:{aapa_obj}\n\tattributes:{attributes} {flags=}')
        attributes = attributes if attributes else self.mapper.attributes(include_key = False)
        for attribute in attributes.copy():
            if not attribute in aapa_obj.relevant_attributes():
                attributes.remove(attribute)
        return self.__find_ids(*self.query_info.get_data(aapa_obj, columns=attributes, flags=flags))
    def find_ids_from_values(self, attributes: list[str], values: list[Any|set[Any]], flags={QIF.ATTRIBUTES})->list[int]:
        self.__db_log('FIND_IDS_FROM_VALUES', f'attributes:{attributes} values:{values} {flags=}')
        return self.__find_ids(*self.query_info.get_data(columns=attributes, values=values, flags=flags))
    def find_max_id(self)->int:
        self.__db_log('FIND_MAX_ID')
        sql = SQLselect(self.mapper.table, columns=['max(id)'])
        if (row := self.database.execute_select(sql)) and row[0][0]:
            return row[0][0]
        return 0
    def find_max_value(self, attribute: str, where:SQE = None)->Any:        
        self.__db_log('FIND_MAX_VALUE', f'attribute:{attribute}  where:{where.db_str() if where else None}')
        col_mapper = self.mapper._find_mapper(attribute)
        sql = SQLselect(self.mapper.table, columns=[f'max({col_mapper.column_name})'], where=where)
        if row:= self.database.execute_select(sql):
            return row[0][0]
        return None 
    # def find_value(self, attributes: str | list[str], values: Any | list[Any])->list[int]:
    #     self.__db_log('FIND_VALUES', f'attributes:{attributes} value: {values}')
    #     where_attributes = attributes if isinstance(attributes, list) else [attributes]
    #     where_values = values if isinstance(values, list) else [values]
    #     return self.find_ids_from_values(where_attributes, where_values)
    def __find_ids(self, where_columns: list[str]=None, where_values: list[Any|set[Any]]=None)->list[int]:
        if where_columns: 
            sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys(), 
                        where=self.__build_where(*(where_columns,where_values)))
        else:
            sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys())
        if rows := self.database.execute_select(sql):
            result = [self.mapper.db_to_value(row['id'], 'id') for row in rows] 
            return result
        return []   
    def __build_where(self, columns: list[str], values: list[Any|set[Any]])->SQE:
        result = None
        log_debug(f'BW: {columns}|{values}')
        for (key,value) in zip(columns, values):
            if isinstance(value, set):
                new_where_part = SQE(key, Ops.IN, list(value), no_column_ref=True)
            else:
                new_where_part = SQE(key, Ops.EQ, value, no_column_ref=True)
            result = new_where_part if not result else SQE(result, Ops.AND, new_where_part)
        return result
    def build_where_from_object(self, aapa_obj: StoredClass, column_names: list[str]=None, flags={QIF.INCLUDE_KEY})->SQE:  
        return self.__build_where(*self.query_info.get_data(aapa_obj, columns=column_names, flags=flags))
    def build_where_from_values(self, column_names: list[str], values: list[Any], flags={QIF.ATTRIBUTES})->SQE:  
        return self.__build_where(*self.query_info.get_data(columns=column_names, values=values, flags=flags))
    def build_where_for_many(self, column_name: str, values: set[Any], flags={QIF.ATTRIBUTES})->SQE:  
        return self.__build_where([column_name], [values])
