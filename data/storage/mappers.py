from typing import Any, Iterable
import sqlite3 as sql3
from data.roots import decode_path, encode_path
from data.storage.storage_const import AAPAClass, DBtype
from database.sql_expr import SQE, Ops
from database.sql_table import SQLselect
from database.table_def import TableDefinition
from general.log import log_debug
from general.timeutil import TSC

class MapperException(Exception): pass

class DBrecord(dict): 
    def __init__(self, table: TableDefinition):
        self.update((column.name, None) for column in table.columns)
        self.table_keys = table.keys
    def clear(self):
        self.update((key,None) for key in self.keys())
    def set_value(self, column_name: str, value: Any):
        self[column_name] = value
    def get_value(self, column_name: str)->Any:
        return self[column_name]
    def set_column_values(self, column_names: Iterable[str], values: list[Any]):
        for column_name, value in zip (column_names, values):
            self.set_value(column_name, value)
    def get_column_values(self, column_names: Iterable[str])->list[Any]:
        return [self[column_name] for column_name in column_names]
    def get_columns(self, include_key = True)->Iterable[str]:
        return self.keys() if include_key else [column_name for column_name in self.keys() if not column_name in self.table_keys]        
    def get_values(self, include_key = True)->Iterable[Any]:
        return self.get_column_values(self.get_columns(include_key))
    def set_values(self, values: Iterable[Any]):
        self.set_column_values(self.get_columns(), values)
    def set_row_values(self, row: sql3.Row):
        self.set_column_values(row.keys(), [row[key] for key in row.keys()])

class ColumnMapper:
    def __init__(self, column_name: str, attribute_name:str=None):
        self.column_name = column_name
        self.attribute_name = attribute_name if attribute_name else column_name
    def map_object_to_db(self, aapa_obj: AAPAClass, db_record: DBrecord):
        db_record.set_value(self.column_name, self.map_value_to_db(getattr(aapa_obj, self.attribute_name)))
    def map_db_to_object(self, db_record: DBrecord)->Any:
        return self.map_db_to_value(db_record.get_value(self.column_name))
    def map_value_to_db(self, value: Any)->DBtype:
        return value
    def map_db_to_value(self, db_value: DBtype)->Any:
        return db_value
    
class IgnoreColumnMapper(ColumnMapper):
    def map_value_to_db(self, value: Any)->DBtype:
        return None
    def map_db_to_value(self, db_value: DBtype)->Any:
        return None

class BoolColumnMapper(ColumnMapper):
    def map_value_to_db(self, value: bool)->DBtype:
        return int(value)
    def map_db_to_value(self, db_value: int)->Any:
        return bool(db_value)

class TimeColumnMapper(ColumnMapper):
    def map_value_to_db(self, value: Any)->DBtype:
        return TSC.timestamp_to_str(value)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return TSC.str_to_timestamp(db_value)

class FilenameColumnMapper(ColumnMapper):
    def map_value_to_db(self, value: Any)->DBtype:
        return encode_path(value)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return decode_path(db_value)

class TableMapper:
    def __init__(self, table: TableDefinition, class_type: AAPAClass):
        self.table = table
        self.db_record = DBrecord(table)
        self.class_type = class_type        
        self._mappers: dict[str,ColumnMapper] = {}     
        for column in self.table.columns:   
            self._mappers[column.name] = ColumnMapper(column.name)
    def mappers(self, column_names: list[str] = None)->list[ColumnMapper]:
        return [mapper for mapper in self._mappers.values() if not column_names or mapper.column_name in column_names]
    def columns(self, include_key = True)->list[str]:
        return [key for key in self._mappers.keys() if include_key or not (key in self.table.keys)]
    def attributes(self, include_key = True)->list[str]:
        return [mapper.attribute_name for key,mapper in self._mappers.items() if include_key or not (key in self.table.keys)]
    def table_keys(self)->list[str]:
        return self.table.keys
    def set_mapper(self, mapper: ColumnMapper):
        self._mappers[mapper.column_name] = mapper
    def set_attribute(self, column_name: str, attribute_name: str):
        self._mappers[column_name].attribute_name = attribute_name
    def object_to_db(self, aapa_obj: AAPAClass, include_key=True, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        log_debug(f'start o2db {column_names=}  {attribute_names=}   {self.columns(include_key)=}')
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns(include_key)
        log_debug(f'{columns=}')
        for column_name in columns:
            self._mappers[column_name].map_object_to_db(aapa_obj, self.db_record)
        return (columns, self.db_record.get_column_values(columns))
    def get_values(self, aapa_obj: AAPAClass, columns: list[str]=None, include_key=True, map_values=True)->list[Any]:
        columns = columns if columns else self.columns(include_key)
        result = []
        for column_name in columns: 
            mapper = self._mappers[column_name]
            value = getattr(aapa_obj,mapper.attribute_name)
            result.append(mapper.map_value_to_db(value) if map_values else value)
        return result
    def values_to_db(self, attribute_values: list[Any], map_values=True, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        #generate paired list of columns/values for database from predefined values, if map_values False or attribute names not supplied: not converted but return directly
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns()
        if map_values:
            attribute_names = attribute_names if attribute_names else [mapper.attribute_name for mapper in self.mappers(columns)]
            values = [self.value_to_db(value, attribute) for value,attribute in zip(attribute_values, attribute_names)]
        else:
            values = attribute_values
        return columns,values
    def value_to_db(self, value: Any, attribute_name: str)->DBtype:
        column_mapper = self._find_mapper(attribute_name)
        return column_mapper.map_value_to_db(value)
    def db_to_object(self, row: sql3.Row, include_key=True)->AAPAClass:
        #generate object from database record
        self.db_record.set_row_values(row)
        return self.__db_to_object(include_key)
    def __db_to_object(self, include_key=True)->AAPAClass:
        #map dbrecord and instantiate a new object
        class_dict = {}
        for column_name in self.columns(include_key):
            mapper = self._mappers[column_name]
            class_dict[mapper.attribute_name] = mapper.map_db_to_object(self.db_record)
        return self.class_type(**class_dict)        
    def _find_mapper(self, attribute_name: str)->ColumnMapper:
        for mapper in self._mappers.values():
            if mapper.attribute_name == attribute_name:
                return mapper
        return None
    def _get_columns_from_attributes(self, attribute_names: list[str]):
        return [self._find_mapper(attribute).column_name for attribute in attribute_names]


# class MapperSearcher:
#     def __init__(self, mapper: TableMapper):
#         self.mapper = mapper
#     def _generate_where_clause(self, columns: list[str], values: list[Any], no_column_ref_for_key=False)->SQE:
#         result = None
#         log_debug(f'GW: {columns}    {values}')
#         for (key,value) in zip(columns, values):
#             log_debug(f'{key} {value}   {result}')
#             new_where_part = SQE(key, Ops.EQ, value, no_column_ref=True)
#             if result is None:
#                 result = new_where_part
#             else:
#                 result = SQE(result, Ops.AND, new_where_part, no_column_ref_for_key=no_column_ref_for_key)
#         return result
#     def generate_where_clause() #abstractify more!
#     def generate_find_SQL(self, aapa_obj: AAPAClass=None, attribute_values: list[Any]=None, map_values = True, where_attribute_names: list[str]=None, where_column_names: list[str]=None, 
#                         columns: list[str] = None, no_column_ref_for_key=False)->SQLselect:
#         columns=columns if columns else self.mapper.table_keys()
#         if aapa_obj:
#             log_debug('start GFSQL')
#             result=SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_object(aapa_obj, include_key=False, attribute_names=where_attribute_names, 
#                                                                                                     column_names=where_column_names), no_column_ref_for_key=no_column_ref_for_key) 
#             log_debug(f'GFSQL{result.query}, {result.parameters}')
#             return result
#         else:
#             return SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_values(attribute_values=attribute_values, map_values=map_values, 
#                                                                                                     attribute_names=where_attribute_names, column_names=where_column_names), 
#                                                                                                     no_column_ref_for_key=no_column_ref_for_key)






# class MapperObjectSearcher(MapperSearcher):
#     def generate_where_clause(self, aapa_obj: AAPAClass, include_key=True, attribute_names: list[str]=None, 
#                                         column_names: list[str]=None, no_column_ref_for_key=False)->SQE:
#         log_debug('start GWfo')
#         result = self._generate_where_clause(*self.mapper.object_to_db(aapa_obj, include_key=include_key, attribute_names=attribute_names, column_names=column_names), no_column_ref_for_key=no_column_ref_for_key)
#         log_debug(f'GW{result.parametrized}, {result.parameters}')
#         return result
#     def generate_find_SQL(self, aapa_obj: AAPAClass=None, attribute_values: list[Any]=None, map_values = True, where_attribute_names: list[str]=None, where_column_names: list[str]=None, 
#                         columns: list[str] = None, no_column_ref_for_key=False)->SQLselect:
#         columns=columns if columns else self.mapper.table_keys()
#         if aapa_obj:
#             log_debug('start GFSQL')
#             result=SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_object(aapa_obj, include_key=False, attribute_names=where_attribute_names, 
#                                                                                                     column_names=where_column_names), no_column_ref_for_key=no_column_ref_for_key) 
#             log_debug(f'GFSQL{result.query}, {result.parameters}')
#             return result
#         else:
#             return SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_values(attribute_values=attribute_values, map_values=map_values, 
#                                                                                                     attribute_names=where_attribute_names, column_names=where_column_names), 
#                                                                                                     no_column_ref_for_key=no_column_ref_for_key)

# class MapperValuesSearcher(MapperSearcher):
#     def generate_where_clause(self, attribute_values: list[Any], map_values=True, attribute_names: list[str]=None, 
#                                         column_names: list[str]=None, no_column_ref_for_key=False)->SQE:
#         return self._generate_where_clause(*self.mapper.values_to_db(attribute_values=attribute_values, map_values=map_values, attribute_names=attribute_names, 
#                                                         column_names=column_names), no_column_ref_for_key=no_column_ref_for_key)


#     def generate_find_SQL(self, aapa_obj: AAPAClass=None, attribute_values: list[Any]=None, map_values = True, where_attribute_names: list[str]=None, where_column_names: list[str]=None, 
#                         columns: list[str] = None, no_column_ref_for_key=False)->SQLselect:
#         columns=columns if columns else self.mapper.table_keys()
#         if aapa_obj:
#             log_debug('start GFSQL')
#             result=SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_object(aapa_obj, include_key=False, attribute_names=where_attribute_names, 
#                                                                                                     column_names=where_column_names), no_column_ref_for_key=no_column_ref_for_key) 
#             log_debug(f'GFSQL{result.query}, {result.parameters}')
#             return result
#         else:
#             return SQLselect(self.mapper.table, columns=columns, where=self.generate_where_clause_from_values(attribute_values=attribute_values, map_values=map_values, 
#                                                                                                     attribute_names=where_attribute_names, column_names=where_column_names), 
#                                                                                                     no_column_ref_for_key=no_column_ref_for_key)

