from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from data.classes.action_log import ActionLog
from data.classes.verslagen import Verslag
from database.sqlexpr import Ops, SQLexpression as SQE
from general.deep_attr import deep_attr_main_part, deep_attr_sub_part, get_deep_attr, has_deep_attr
from database.database import Database
from database.tabledef import TableDefinition
from general.keys import get_next_key
from general.log import log_debug

DBtype = type[str|int|float]
AAPAClass = type[Bedrijf|Student|File|Files|Aanvraag|ActionLog|Verslag]
KeyClass = type[int|str]
class CRUDbase:    
    def __init__(self, database: Database, table: TableDefinition, class_type: AAPAClass, no_column_ref_for_key = False):
        self.database = database
        self.table = table
        self.no_column_ref_for_key = no_column_ref_for_key
        self._db_map = {column.name: {'attrib':column.name, 'obj2db': None, 'db2obj': None} for column in table.columns}
        self.class_type = class_type
    def _get_all_columns(self, include_key = True)->list[str]:
        return([column.name for column in self.table.columns if include_key or (not column.is_primary())])
    def __get_column_value(self, aapa_obj: AAPAClass, column_name: str):
        return self.map_object_to_db(column_name, get_deep_attr(aapa_obj, self._db_map[column_name]['attrib'], '???'))
    def _get_key_values(self, aapa_obj: AAPAClass)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, key) for key in self.table.keys]
    def _get_all_values(self, aapa_obj: AAPAClass, include_key = True)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, column_name) for column_name in self._get_all_columns(include_key)]
    def __map_column(self, column_name: str, value, map_name):
        converter = self._db_map[column_name][map_name]        
        return converter(value) if converter else value
    def map_object_to_db(self, column_name: str, value)->DBtype:
        return self.__map_column(column_name, value, 'obj2db')        
    def map_db_to_object(self, column_name: str, value):
        return self.__map_column(column_name, value, 'db2obj')
    def create(self, aapa_obj: AAPAClass):
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(aapa_obj)) 
    def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->AAPAClass: 
        #placeholder for reading attribs that are actually Stored Classes, at this moment only Aanvraag needs this
        return None
    def read(self, key: KeyClass, multiple=False)->type[AAPAClass|list]:
        if rows := self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.map_object_to_db(self.table.key, key), no_column_ref=self.no_column_ref_for_key)):
            if multiple:
                return rows
            else:
                class_dict = {self._db_map[column.name]['attrib']: self.map_db_to_object(column.name, rows[0][column.name]) for column in self.table.columns}
                new_dict = {}
                for attr, value in class_dict.items():
                    if has_deep_attr(attr):
                        new_dict[attr] = {'new_attr': deep_attr_main_part(attr), 'new_value': self._read_sub_attrib(deep_attr_main_part(attr), deep_attr_sub_part(attr), value)}
                for attr, record in new_dict.items():
                    class_dict[record['new_attr']] = record['new_value'] 
                    del class_dict[attr]
                return self.class_type(**class_dict)
        return None 
    def update(self, aapa_obj: AAPAClass):
        where = None
        for key,value in zip(self.table.keys, self._get_key_values(aapa_obj)):
            new_where_part = SQE(key, Ops.EQ, value, no_column_ref=self.no_column_ref_for_key)
            if where is None:
                where = new_where_part
            else:
                where = SQE(where, Ops.AND, new_where_part)
        self.database.update_record(self.table, columns=self._get_all_columns(False), values=self._get_all_values(aapa_obj, False), where=where)
    def delete(self, value: DBtype):
        key = self.table.key
        attrib = self._db_map[key]['attrib']
        self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self.map_object_to_db(attrib, value), no_column_ref=self.no_column_ref_for_key))


class CRUDbaseAuto(CRUDbase):
    #table with integer primary key. This is done by pre-setting the id 
    def create(self, aapa_obj: AAPAClass):   
        setattr(aapa_obj, self.table.key, get_next_key(self.table.name)) 
        super().create(aapa_obj)
