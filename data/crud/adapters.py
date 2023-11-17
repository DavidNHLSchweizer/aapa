from typing import Any, Iterable
import sqlite3 as sql3
from data.crud.crud_const import AAPAClass, DBtype, KeyClass
from data.roots import decode_path, encode_path
from database.sql_expr import SQE, Ops
from database.sql_table import SQLselect
from database.table_def import TableDefinition
from general.timeutil import TSC

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

class ColumnAdapter:
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
    
class IgnoreColumnAdapter(ColumnAdapter):
    def map_value_to_db(self, value: Any)->DBtype:
        return None
    def map_db_to_value(self, db_value: DBtype)->Any:
        return None

class BoolColumnAdapter(ColumnAdapter):
    def map_value_to_db(self, value: bool)->DBtype:
        return int(value)
    def map_db_to_value(self, db_value: int)->Any:
        return bool(db_value)

class TimeColumnAdapter(ColumnAdapter):
    def map_value_to_db(self, value: Any)->DBtype:
        return TSC.timestamp_to_str(value)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return TSC.str_to_timestamp(db_value)

class FilenameColumnAdapter(ColumnAdapter):
    def map_value_to_db(self, value: Any)->DBtype:
        return encode_path(value)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return decode_path(db_value)

class TableAdapter:
    def __init__(self, table: TableDefinition, class_type: AAPAClass):
        self.table = table
        self.db_record = DBrecord(table)
        self.class_type = class_type        
        self._adapters: dict[str,ColumnAdapter] = {}     
        for column in self.table.columns:   
            self._adapters[column.name] = ColumnAdapter(column.name)
    def adapters(self, column_names: list[str] = None)->list[ColumnAdapter]:
        return [adapter for adapter in self._adapters.values() if not column_names or adapter.column_name in column_names]
    def columns(self, include_key = True)->list[str]:
        return [key for key in self._adapters.keys() if include_key or not (key in self.table.keys)]
    def table_keys(self)->list[str]:
        return self.table.keys
    def set_adapter(self, adapter: ColumnAdapter):
        self._adapters[adapter.column_name] = adapter
    def set_attribute(self, column_name: str, attribute_name: str):
        self._adapters[column_name].attribute_name = attribute_name
    def keys_to_db(self, aapa_obj: AAPAClass)->tuple[list[str], list[Any]]:
        return self.object_to_db(aapa_obj, column_names=self.table_keys)
    def object_to_db(self, aapa_obj: AAPAClass, include_key=True, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns(include_key)
        for column_name in columns:
            self._adapters[column_name].map_object_to_db(aapa_obj, self.db_record)
        return (columns, self.db_record.get_column_values(columns))
    def values_to_db(self, attribute_values: list[Any], map_values=True, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        #generate list of values for database from predefined values, if attribute names not supplied: not converted but return directly
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns()
        if map_values:
            attribute_names = attribute_names if attribute_names else [adapter.attribute_name for adapter in self.adapters(columns)]
            values = [self.value_to_db(value, attribute) for value,attribute in zip(attribute_values, attribute_names)]
        else:
            values = attribute_values
        return columns,values
    def value_to_db(self, value: Any, attribute_name: str)->DBtype:
        column_adapter = self._find_adapter(attribute_name)
        return column_adapter.map_value_to_db(value)
    def db_to_object(self, row: sql3.Row, include_key=True)->AAPAClass:
        self.db_record.set_row_values(row)
        return self._db_to_object(include_key)
    def _db_to_object(self, include_key=True)->AAPAClass:
        class_dict = {}
        for column_name in self.columns(include_key):
            adapter = self._adapters[column_name]
            class_dict[adapter.attribute_name] = adapter.map_db_to_object(self.db_record)
        return self.class_type(**class_dict)        
    def _find_adapter(self, attribute_name: str)->ColumnAdapter:
        for adapter in self._adapters.values():
            if adapter.attribute_name == attribute_name:
                return adapter
        return None
    def _get_columns_from_attributes(self, attribute_names: list[str]):
        return [self._find_adapter(attribute).column_name for attribute in attribute_names]


def _generate_where_clause(columns: list[str], values: list[Any], no_column_ref_for_key=False)->SQE:
    result = None
    for (key,value) in zip(columns, values):
        new_where_part = SQE(key, Ops.EQ, value, no_column_ref_for_key=no_column_ref_for_key)
        if result is None:
            result = new_where_part
        else:
            result = SQE(result, Ops.AND, new_where_part, no_column_ref_for_key=no_column_ref_for_key)
    return result

def generate_where_clause_from_object(adapter: TableAdapter, aapa_obj: AAPAClass, include_key=True, attribute_names: list[str]=None, 
                                      column_names: list[str]=None, no_column_ref_for_key=False)->SQE:
    return _generate_where_clause(*adapter.object_to_db(aapa_obj, include_key=include_key, attribute_names=attribute_names, column_names=column_names), no_column_ref_for_key=no_column_ref_for_key)

def generate_where_clause_from_values(adapter: TableAdapter, attribute_values: list[Any], map_values=True, attribute_names: list[str]=None, 
                                      column_names: list[str]=None, no_column_ref_for_key=False)->SQE:
    return _generate_where_clause(*adapter.values_to_db(attribute_values=attribute_values, map_values=map_values, attribute_names=attribute_names, 
                                                       column_names=column_names), no_column_ref_for_key=no_column_ref_for_key)


def generate_find_SQL(adapter: TableAdapter, aapa_obj: AAPAClass=None, attribute_values: list[Any]=None, map_values = True, where_attribute_names: list[str]=None, where_column_names: list[str]=None, 
                       columns: list[str] = None, no_column_ref_for_key=False)->SQLselect:
    columns=columns if columns else adapter.table_keys()
    if aapa_obj:
        return SQLselect(adapter.table, columns=columns, where=generate_where_clause_from_object(adapter, aapa_obj, include_key=False, attribute_names=where_attribute_names, 
                                                                                                 column_names=where_column_names), no_column_ref_for_key=no_column_ref_for_key)
    else:
        return SQLselect(adapter.table, columns=columns, where=generate_where_clause_from_values(adapter, attribute_values=attribute_values, map_values=map_values, 
                                                                                                 attribute_names=where_attribute_names, column_names=where_column_names), 
                                                                                                 no_column_ref_for_key=no_column_ref_for_key)

