from typing import Any, Iterable, Type
import sqlite3 as sql3
from data.classes.aapa_class import AAPAclass
from data.roots import decode_path, encode_path
from data.storage.general.storage_const import StorageException, StoredClass, DBtype
from database.database import Database
from database.table_def import TableDefinition
from general.classutil import classname
from general.timeutil import TSC

class MapperException(Exception): pass
class ObjRecord(dict): 
    def __init__(self, columns: list[str]):
        self.update((column, None) for column in columns)
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
    def set_dict_values(self, values: dict[str,Any]):
        self.set_column_values(values.keys(), values.values())

class ColumnMapper:
    def __init__(self, column_name: str, attribute_name:str=None, 
                 db_to_obj:Type[Any]=None, obj_to_db: Type[Any]=None):
        self.column_name = column_name
        self.attribute_name = attribute_name if attribute_name else column_name
        self.__db_to_obj = db_to_obj
        self.__obj_to_db = obj_to_db
    def map_object_to_db(self, aapa_obj: StoredClass, db_record: ObjRecord):
        db_record.set_value(self.column_name, self.map_value_to_db(getattr(aapa_obj, self.attribute_name)))
    def map_db_to_object(self, db_record: ObjRecord)->Any:
        return self.map_db_to_value(db_record.get_value(self.column_name))
    def map_value_to_db(self, value: Any)->DBtype:
        if not self.__obj_to_db:
            return value
        else:
            if isinstance(value, set):
                return set(self.map_value_to_db(val) for val in value)
            else:
                return self.__obj_to_db(value)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return db_value if not self.__db_to_obj else self.__db_to_obj(db_value)
ColumnMapperType = type[ColumnMapper]

class IgnoreColumnMapper(ColumnMapper):
    def map_value_to_db(self, value: Any)->DBtype:
        return None
    def map_db_to_value(self, db_value: DBtype)->Any:
        return None

class BoolColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str=None):
        super().__init__(column_name=column_name, attribute_name=attribute_name, 
                         db_to_obj=bool, obj_to_db=int)

class TimeColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str=None):
        super().__init__(column_name=column_name, attribute_name=attribute_name, 
                         db_to_obj=TSC.sortable_str_to_timestamp, 
                         obj_to_db=TSC.timestamp_to_sortable_str)
            
class FilenameColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str=None):
        super().__init__(column_name=column_name, attribute_name=attribute_name, 
                         db_to_obj=decode_path, 
                         obj_to_db=encode_path)

class ObjectMapper:
    def __init__(self, columns: list[str], class_type: AAPAclass):
        self.columns=columns
        self.obj_record = ObjRecord(columns)
        self.class_type = class_type        
        self._mappers = {column: self._init_column_mapper(column) for column in columns}
        for column in self.columns:
            if not self._mappers[column]:
                raise MapperException(f'Invalid mapper for column [{column}] in ObjectMapper for {classname(self.class_type)}')
    def _init_column_mapper(self, column_name: str)->ColumnMapper:
        return ColumnMapper(column_name) # customize for non-default columns
    def mappers(self, column_names: list[str] = None)->list[ColumnMapper]:
        return [mapper for mapper in self._mappers.values() if not column_names or mapper.column_name in column_names]
    def attributes(self)->list[str]:
        return [mapper.attribute_name for mapper in self._mappers.values()]
    def set_mapper(self, mapper: ColumnMapper):
        self._mappers[mapper.column_name] = mapper
    def set_attribute(self, column_name: str, attribute_name: str):
        self._mappers[column_name].attribute_name = attribute_name
    def object_to_db(self, aapa_obj: AAPAclass, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns
        for column_name in columns:
            self._mappers[column_name].map_object_to_db(aapa_obj, self.obj_record)
        return (columns, self.obj_record.get_column_values(columns))
    def get_values(self, aapa_obj: AAPAclass, columns: list[str]=None, map_values=True)->list[Any]:
        columns = columns if columns else self.columns
        result = []
        for column_name in columns: 
            mapper = self._mappers[column_name]
            value = getattr(aapa_obj,mapper.attribute_name)
            result.append(mapper.map_value_to_db(value) if map_values else value)
        return result
    def values_to_db(self, attribute_values: list[Any], map_values=True, attribute_names: list[str]=None, column_names: list[str]=None)->tuple[list[str], list[Any]]:
        #generate paired list of columns/values for database from predefined values, if map_values False or attribute names not supplied: not converted but return directly
        columns = column_names if column_names else self._get_columns_from_attributes(attribute_names) if attribute_names else self.columns
        if map_values:
            attribute_names = attribute_names if attribute_names else [mapper.attribute_name for mapper in self.mappers(columns)]
            values = [self.value_to_db(value, attribute) for value,attribute in zip(attribute_values, attribute_names)]
        else:
            values = attribute_values
        return columns,values
    def value_to_db(self, value: Any, attribute_name: str)->Any:
        column_mapper = self._find_mapper(attribute_name)
        return column_mapper.map_value_to_db(value)
    def db_to_value(self, value: Any, attribute_name: str)->Any:
        column_mapper = self._find_mapper(attribute_name)
        return column_mapper.map_db_to_value(value)
    def db_to_object(self, values: dict[str,Any])->AAPAclass:
        #generate object from database record
        self.obj_record.set_dict_values(values)
        return self.__db_to_object()
    def __db_to_object(self)->AAPAclass:
        #map dbrecord and instantiate a new object
        class_dict = {}
        for column_name in self.columns:
            mapper = self._mappers[column_name]
            class_dict[mapper.attribute_name] = mapper.map_db_to_object(self.obj_record)
        return self.class_type(**class_dict)        
    def _find_mapper(self, attribute_name: str)->ColumnMapper:
        for mapper in self._mappers.values():
            if mapper.attribute_name == attribute_name:
                return mapper
        return None
    def _get_columns_from_attributes(self, attribute_names: list[str]):
        return [self._find_mapper(attribute).column_name for attribute in attribute_names]

