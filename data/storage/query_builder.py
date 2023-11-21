from __future__ import annotations
from enum import Enum
from typing import Any
from data.crud.mappers import MapperException, TableMapper
from data.storage.storage_const import AAPAClass
from database.database import Database
from database.sql_expr import SQE, Ops
from database.sql_table import SQLselect
from general.log import log_debug

class QueryInfo:
    class Flags(Enum):
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
    def __get_values(self, data_columns: list[str], aapa_obj: AAPAClass, values: list[Any], no_map_values: bool):
        if values:
            if len(values) != len(data_columns):
                raise MapperException(f'Invalid parameters: {len(data_values)} data_values, but {len(data_columns)} columns')              
            if no_map_values:
                data_values = values
            else:
                data_values = [self.mapper._mappers[column_name].map_value_to_db(value)  
                                    for column_name,value in zip[data_columns, values]]
        else: # get values from object
            if not aapa_obj:
                raise MapperException(f'Invalid parameters: provide either an object or values.')
            data_values = []
            for column_name in data_columns:
                mapper = self.mapper._mappers[column_name]
                value = getattr(aapa_obj, mapper.attribute_name)
                data_values.append(value if no_map_values else mapper.map_value_to_db(value))
    def get_data(self, aapa_obj: AAPAClass = None, columns: list[str] = [], values: list[Any] = [], 
                 flags = {Flags.INCLUDE_KEY, Flags.NO_MAP_VALUES}):
        data_columns = self.__get_columns(columns, flags)
        data_values = self.__get_values(aapa_obj, values, QueryInfo.no_map_values(flags)) 
        return data_columns, data_values
QIF = QueryInfo.Flags

class QueryBuilder:
    def __init__(self, database: Database, mapper: TableMapper):
        self.database = database
        self.mapper = mapper
        self.query_info = QueryInfo(mapper)
    def find_id(self, aapa_obj: AAPAClass, attributes: list[str] = None)->list[int]:
        attributes = attributes if attributes else self.mapper.attributes(include_key = False)
        return self.__find_id(*self.query_info.get_data(aapa_obj, columns=attributes, flags={QIF.ATTRIBUTES}))
        # where_columns,where_values = 
        # sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys(), where=self.__build_where(where_columns, where_values))
        # log_debug(f'FINDID: {sql.query}, {sql.parameters}')
        # if rows := self.database.execute_select(sql):
        #     return self.mapper.db_to_object(rows[0]).id 
        # return None   
    def find_id_from_values(self, attributes: list[str], values: list[Any])->list[int]:
        return self.__find_id(*self.query_info.get_data(columns=attributes, values=values, flags={QIF.ATTRIBUTES}))
        # where_columns,where_values = self.query_info.get_data(columns=attributes, values=values, flags={QIF.ATTRIBUTES})
        # sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys(), where=self.__build_where(where_columns, where_values))
        # log_debug(f'FINDID: {sql.query}, {sql.parameters}')
        # if rows := self.database.execute_select(sql):
        #     return self.mapper.db_to_object(rows[0]).id 
        # return None   
    def __find_id(self, where_columns: list[str], where_values: list[Any])->list[int]:
        sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys(), where=self.__build_where(*(where_columns,where_values)))
        log_debug(f'FINDID: {sql.query}, {sql.parameters}')
        if rows := self.database.execute_select(sql):
            return self.mapper.db_to_object(rows[0]).id 
        return None   


    def __build_where(self, columns: list[str], values: list[Any])->SQE:
        result = None
        for (key,value) in zip(columns, values):
            new_where_part = SQE(key, Ops.EQ, value, no_column_ref=True)
            result = new_where_part if not result else SQE(result, Ops.AND, new_where_part)
        return result
    def build_where(self, aapa_obj: AAPAClass, column_names: list[str]=None, flags={QIF.INCLUDE_KEY})->SQE:  
        return self.__build_where(*self.query_info.get_data(aapa_obj, column_names, flags))
    
        # return self.__build_where(*self.mapper.object_to_db(aapa_obj, include_key=include_key, 
        #                          attribute_names=attribute_names, column_names=column_names))

    # def find_object(self, aapa_obj: AAPAClass)->list[int]:      
    #     columns,values = self.__get_columns_and_values(aapa_obj, include_key=False, map_values=True, 
    #                                                    attribute_names=self.mapper.attributes())
    #     sql = SQLselect(self.mapper.table, columns=columns, where=self.__generate_where_clause(columns, values))
    #     log_debug(f'FINDOBJECT: {sql.query}, {sql.parameters}')
    #     if rows := self.database.execute_select(sql):
    #         return self.mapper.db_to_object(rows[0]) 
    #     return None   
    # def __get_columns_and_values(self, aapa_obj: AAPAClass, include_key = False, map_values=True, 
    #                              column_names: list[str]=None, attribute_names: list[str] = None)->Tuple[list[str], list[str]]:
    #     columns = column_names if column_names else self.mapper._get_columns_from_attributes(attribute_names) if attribute_names else self.mapper.columns(include_key)        
    #     values = self.mapper.get_values(aapa_obj, columns, include_key=include_key, map_values=map_values)
    #     return (columns, values)






    # def find_object(self, aapa_obj: AAPAClass)->AAPAClass:
    #     if rows := self.database.execute_select(self._generate_find_SQL_from_object(aapa_obj)):
    #         return self.mapper.db_to_object(rows[0])
    #     return None
    # def find_from_values(self, attribute_names: list[str], attribute_values: list[Any])->AAPAClass:
    #     if rows := self.database.execute_select(self._generate_find_SQL_from_values(attribute_names=attribute_names, attribute_values=attribute_values)):
    #         return self.mapper.db_to_object(rows[0])
    #     return None



    #     log_debug('start GWfo')
    #     result = self._generate_where_clause(*self.mapper.object_to_db(aapa_obj, include_key=include_key, attribute_names=attribute_names, column_names=column_names), no_column_ref_for_key=no_column_ref_for_key)
    #     log_debug(f'GW{result.parametrized}, {result.parameters}')
    #     return result
    # def generate_find_SQL(self, aapa_obj: AAPAClass=None, attribute_values: list[Any]=None, map_values = True, where_attribute_names: list[str]=None, where_column_names: list[str]=None, 
    #                     columns: list[str] = None, no_column_ref_for_key=False)->SQLselect:
    #     columns=columns if columns else self.mapper.table_keys()
    #     if aapa_obj:
    #         log_debug('start GFSQL')
    #         result=SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_object(aapa_obj, include_key=False, attribute_names=where_attribute_names, 
    #                                                                                                 column_names=where_column_names), no_column_ref_for_key=no_column_ref_for_key) 
    #         log_debug(f'GFSQL{result.query}, {result.parameters}')
    #         return result
    #     else:
    #         return SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_values(attribute_values=attribute_values, map_values=map_values, 
    #                                                                                                 attribute_names=where_attribute_names, column_names=where_column_names), 
    #                                                                                                 no_column_ref_for_key=no_column_ref_for_key)
