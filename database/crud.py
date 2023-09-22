from typing import Iterable
from data.classes.aanvragen import AanvraagInfo
from data.classes.bedrijven import Bedrijf
from data.classes.files import FileInfo
from data.classes.studenten import StudentInfo
from data.classes.process_log import ProcessLog
from database.sqlexpr import Ops, SQLexpression as SQE
from general.deep_attr import get_deep_attr
from database.database import Database
from database.tabledef import TableDefinition
from general.log import log_debug

DBtype = type[str|int|float]
StoredClass = type[AanvraagInfo|Bedrijf|StudentInfo|FileInfo|ProcessLog]
class CRUDbase:
    
    def __init__(self, database: Database, table: TableDefinition, class_type: StoredClass, no_column_ref_for_key = False):
        self.database = database
        self.table = table
        self.no_column_ref_for_key = no_column_ref_for_key
        self._db_map = {column.name: {'attrib':column.name, 'obj2db': None, 'db2obj': None} for column in table.columns}
        self.class_type = class_type
        # print(self._db_map)
    def _get_all_columns(self, include_key = True):
        result = []
        if include_key:
            result.extend(self.table.keys)
        result.extend([column.name for column in self.table.columns if not column.is_primary()])
        return result
    def _get_all_values(self, obj: object, include_key = True)->Iterable[DBtype]:
        result = []
        for column in self.table.columns:
            if include_key or not column.is_primary():
                result.append(self.map_object_to_db(column.name, 
                                                    get_deep_attr(obj, self._db_map[column.name]['attrib'], '???')))
        return result
    # def controle(self, oldarray: list[str], include_key=True):
    #     vergelijk = self._get_all_columns(include_key=include_key)
    #     if len(vergelijk) != len(oldarray):
    #         print(f'foutje bedankt: {self.table.table_name}... {str(vergelijk)} != {str(oldarray)}')
    #         return
    #     for r, v in zip(oldarray, vergelijk):
    #         if r!= v:
    #             print(f'shit {self.table.table_name}: {r} != {v}')
    # def controle2(self, oldarray: list[DBtype], obj: object, include_key=True):
    #     vergelijk = self._get_all_values(obj, include_key=include_key)
    #     print(vergelijk)
    #     # print(f'include key: {include_key}')
    #     # print(oldarray)
    #     # print(vergelijk)
    #     if len(vergelijk) != len(oldarray):
    #         print(f'foutje verdankt : {self.table.table_name}... {str(vergelijk)} != {str(oldarray)}')
    #         return
    #     for r, v in zip(oldarray, vergelijk):
    #         if r!= v:
    #             print(f'shit {self.table.table_name}: {r} != {v}')
    def __map_column(self, column_name: str, value, map_name):
        converter = self._db_map[column_name][map_name]        
        return converter(value) if converter else value
    def map_object_to_db(self, column_name: str, value)->DBtype:
        return self.__map_column(column_name, value, 'obj2db')        
    def map_db_to_object(self, column_name: str, value):
        return self.__map_column(column_name, value, 'db2obj')
    def create(self, obj: object):
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(obj)) 
    def read(self, key, multiple=False)->object:
        if rows := self.database.read_record(self.table, where=SQE(self.table.keys[0], Ops.EQ, self.map_object_to_db(self.table.keys[0], key), no_column_ref=self.no_column_ref_for_key)):
            if multiple:
                raise(f'DOE IETS!!! RETURNING multiple {rows}')
                return rows
            else:
                class_dict = {self._db_map[column.name]['attrib']: self.map_db_to_object(column.name, rows[0][column.name]) for column in self.table.columns}
                return self.class_type(**class_dict)
            # rows[0]
        
        # if self.no_column_ref_for_key:
        #     log_debug(f'UNEXPECTED')
        return None 
    def update(self, **kwargs):
        self.database.update_record(self.table, **kwargs)
    # def delete(self, **kwargs):
    #     self.database.delete_record(self.table, **kwargs)
    def delete(self, value: DBtype):
        key = self.table.keys[0]
        attrib = self._db_map[key]['attrib']
        self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self.map_object_to_db(attrib, value)))