from typing import Any, Tuple
from data.crud.crud_const import AAPAClass
from data.crud.mappers import TableMapper
from database.database import Database
from database.sql_expr import SQE, Ops
from database.sql_table import SQLselect
from general.log import log_debug

class TableSearcher:
    def __init__(self, database: Database, mapper: TableMapper):
        self.database = database
        self.mapper = mapper
    def find_id(self, aapa_obj: AAPAClass, attributes: list[str] = None)->list[int]:
        attributes = attributes if attributes else self.mapper.attributes(include_key = False)
        columns,values = self.__get_columns_and_values(aapa_obj, include_key=False, map_values=True, attribute_names=attributes)
        sql = SQLselect(self.mapper.table, columns=self.mapper.table_keys(), where=self.__generate_where_clause(columns, values))
        log_debug(f'TABLESEARCH: {sql.query}, {sql.parameters}')
        if rows := self.database.execute_select(sql):
            return self.mapper.db_to_object(rows[0]) 
        return None   
    def __get_columns_and_values(self, aapa_obj: AAPAClass, include_key = False, map_values=True, 
                                 column_names: list[str]=None, attribute_names: list[str] = None)->Tuple[list[str], list[str]]:
        columns = column_names if column_names else self.mapper._get_columns_from_attributes(attribute_names) if attribute_names else self.mapper.columns(include_key)        
        values = self.mapper.get_values(aapa_obj, columns, include_key=include_key, map_values=map_values)
        return (columns, values)
    def __generate_where_clause(self, columns: list[str], values: list[Any])->SQE:
        result = None
        for (key,value) in zip(columns, values):
            new_where_part = SQE(key, Ops.EQ, value, no_column_ref=True)
            result = new_where_part if not result else SQE(result, Ops.AND, new_where_part)
        return result

    # def generate_where_clause(self, aapa_obj: AAPAClass, include_key=True, attribute_names: list[str]=None, 
    #                                     column_names: list[str]=None)->SQE:
        
    #     self.mapper.object_to_db





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
