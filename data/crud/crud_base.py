from __future__ import annotations
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from data.classes.action_log import ActionLog
from data.classes.verslagen import Verslag
from database.sql_expr import Ops, SQE
from database.view_def import ViewDefinition
from debug.debug import classname
from general.deep_attr import deep_attr_main_part, deep_attr_sub_part, get_deep_attr, has_deep_attr
from database.database import Database
from database.table_def import TableDefinition
from general.keys import get_next_key
from general.log import log_debug

DBtype = type[str|int|float]
AAPAClass = type[Bedrijf|Student|File|Files|Aanvraag|ActionLog|Verslag]
KeyClass = type[int|str]
class CRUDbase:    
    #base class also supporting views for reading (SQLite views only support reading)
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                 view: ViewDefinition = None, details: list[CRUDbase] = [], no_column_ref_for_key = False, autoID=False):
        self.database = database
        self.table = table
        self.view = view
        self.details = details
        self._db_map = {column_name: {'attrib':column_name, 'obj2db': None, 'db2obj': None} for column_name in self._get_all_columns(use_view=True)}
        self.class_type = class_type
        self.no_column_ref_for_key = no_column_ref_for_key
        self.autoID = autoID
    def _get_all_columns(self, include_key = True, use_view=False)->list[str]:
        if self.view and use_view:
            return self.view.column_names
        else:
            return([column.name for column in self.table.columns if include_key or (not column.is_primary())])
    def get_keys(self)->Iterable[str]:
        if self.view:
            return self.view.get_keys()
        else:
            return self.table.keys
    def __get_column_value(self, aapa_obj: AAPAClass, column_name: str):
        return self.map_object_to_db(column_name, get_deep_attr(aapa_obj, self._db_map[column_name]['attrib'], '???'))
    def _get_key_values(self, aapa_obj: AAPAClass)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, key) for key in self.get_keys()]
    def _get_all_values(self, aapa_obj: AAPAClass, include_key = True, use_view=False)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, column_name) for column_name in self._get_all_columns(include_key=include_key, use_view=use_view)]
    def __map_column(self, column_name: str, value, map_name):
        converter = self._db_map[column_name][map_name]        
        return converter(value) if converter else value
    def map_object_to_db(self, column_name: str, value)->DBtype:
        return self.__map_column(column_name, value, 'obj2db')        
    def map_db_to_object(self, column_name: str, value):
        return self.__map_column(column_name, value, 'db2obj')
    def create(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD({classname(self)}) create {str(aapa_obj)}')
        if self.autoID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name)) 
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(aapa_obj)) 
        for detail_CRUD in self.details:
            detail_CRUD.create(aapa_obj)
    def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->AAPAClass: 
        #placeholder for reading attribs that are actually Stored Classes, at this moment only Milestone needs this
        return None    
    def read_records(self, key: KeyClass)->type[AAPAClass|list]:
        if self.view:
            return self.database.read_view_record(self.view,where=SQE(self.view.key, Ops.EQ, self.map_object_to_db(self.view.key, key)))
        else:
            return self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.map_object_to_db(self.table.key, key), 
                                                                                    no_column_ref=self.no_column_ref_for_key))
    def read(self, key: KeyClass, multiple=False)->type[AAPAClass|list]:
        log_debug(f'CRUD({classname(self)}) read {key}')
        #NOTE: dit nog aanpassen aan details, maar misschien hoeft dat niet als er altijd een VIEW is in dat geval?!
        if rows := self.read_records(key):
            if multiple:
                return rows
            else:
                class_dict = {self._db_map[column_name]['attrib']: self.map_db_to_object(column_name, rows[0][column_name]) 
                              for column_name in self._get_all_columns(use_view=True)}
                new_dict = {}
                for attr, value in class_dict.items():
                    if has_deep_attr(attr):
                        new_dict[attr] = {'new_attr': deep_attr_main_part(attr), 'new_value': self._read_sub_attrib(deep_attr_main_part(attr), deep_attr_sub_part(attr), value)}
                for attr, record in new_dict.items():
                    class_dict[record['new_attr']] = record['new_value'] 
                    del class_dict[attr]                
                log_debug(f'CLASSDICT:{str(class_dict)}')
                return self.class_type(**class_dict)
        return None 
    def update(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD({classname(self)}) update {str(aapa_obj)}')
        where = None
        for key,value in zip(self.table.keys, self._get_key_values(aapa_obj)):
            new_where_part = SQE(key, Ops.EQ, value, no_column_ref=self.no_column_ref_for_key)
            if where is None:
                where = new_where_part
            else:
                where = SQE(where, Ops.AND, new_where_part)
        self.database.update_record(self.table, columns=self._get_all_columns(include_key=False), 
                                    values=self._get_all_values(aapa_obj, include_key=False), where=where)
        for detail_CRUD in self.details:
            detail_CRUD.update(aapa_obj)
    def delete(self, value: DBtype):
        log_debug(f'CRUD({classname(self)}) delete {str(value)}')
        for detail_CRUD in self.details:
            detail_CRUD.delete(value)
        key = self.table.key
        attrib = self._db_map[key]['attrib']
        self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self.map_object_to_db(attrib, value), no_column_ref=self.no_column_ref_for_key))
