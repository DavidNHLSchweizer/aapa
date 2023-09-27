from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from data.classes.action_log import ActionLog
from database.sqlexpr import Ops, SQLexpression as SQE
from general.deep_attr import deep_attr_main_part, deep_attr_sub_part, get_deep_attr, has_deep_attr
from database.database import Database
from database.tabledef import TableDefinition
from general.log import log_debug

DBtype = type[str|int|float]
AAPAClass = type[Bedrijf|Student|File|Files|Aanvraag|ActionLog]
KeyClass = type[int|str]
class CRUDbase:    
    def __init__(self, database: Database, table: TableDefinition, class_type: AAPAClass, no_column_ref_for_key = False):
        self.database = database
        self.table = table
        self.no_column_ref_for_key = no_column_ref_for_key
        self._db_map = {column.name: {'attrib':column.name, 'obj2db': None, 'db2obj': None} for column in table.columns}
        self.class_type = class_type
    def _get_all_columns(self, include_key = True):
        result = []
        if include_key:
            result.extend(self.table.keys)
        result.extend([column.name for column in self.table.columns if not column.is_primary()])
        return result
    def __get_column_value(self, obj: AAPAClass, column_name: str):
        return self.map_object_to_db(column_name, get_deep_attr(obj, self._db_map[column_name]['attrib'], '???'))
    def _get_key_values(self, obj: AAPAClass)->Iterable[DBtype]:
        result = []
        for column in self.table.columns:
            if column.is_primary():
                result.append(self.__get_column_value(obj, column.name))
        return result
    def _get_all_values(self, obj: AAPAClass, include_key = True)->Iterable[DBtype]:
        result = []
        for column in self.table.columns:
            if include_key or not column.is_primary():
                result.append(self.__get_column_value(obj, column.name))
        return result
    def __map_column(self, column_name: str, value, map_name):
        converter = self._db_map[column_name][map_name]        
        return converter(value) if converter else value
    def map_object_to_db(self, column_name: str, value)->DBtype:
        return self.__map_column(column_name, value, 'obj2db')        
    def map_db_to_object(self, column_name: str, value):
        return self.__map_column(column_name, value, 'db2obj')
    def create(self, obj: AAPAClass):
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(obj)) 
    def _read_sub_attrib(self, sub_attrib_name: str, value)->AAPAClass: 
        #placeholder for reading attribs that are actually Stored Classes , at this moment Aanvraag needs this
        return None
    def read(self, key: KeyClass, multiple=False)->AAPAClass:
        if rows := self.database.read_record(self.table, where=SQE(self.table.keys[0], Ops.EQ, self.map_object_to_db(self.table.keys[0], key), no_column_ref=self.no_column_ref_for_key)):
            if multiple:
                return rows
            else:
                class_dict = {self._db_map[column.name]['attrib']: self.map_db_to_object(column.name, rows[0][column.name]) for column in self.table.columns}
                new_dict = {}
                for attr, value in class_dict.items():
                    if has_deep_attr(attr):
                        new_dict[attr] = {'new_attr': deep_attr_main_part(attr), 'new_value': self._read_sub_attrib(deep_attr_sub_part(attr), value)}
                for attr, record in new_dict.items():
                    class_dict[record['new_attr']] = record['new_value'] 
                    del class_dict[attr]
                return self.class_type(**class_dict)
        return None 
    def update(self, obj: AAPAClass):
        where = None
        for key,value in zip(self.table.keys, self._get_key_values(obj)):
            new_where_part = SQE(key, Ops.EQ, value, no_column_ref=self.no_column_ref_for_key)
            if where is None:
                where = new_where_part
            else:
                where = SQE(where, Ops.AND, new_where_part)
        self.database.update_record(self.table, columns=self._get_all_columns(False), values=self._get_all_values(obj, False), where=where)
    def delete(self, value: DBtype):
        key = self.table.keys[0]
        attrib = self._db_map[key]['attrib']
        self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self.map_object_to_db(attrib, value), no_column_ref=self.no_column_ref_for_key))