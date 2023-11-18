# from __future__ import annotations
# from abc import abstractmethod
# from dataclasses import dataclass
# from enum import Enum, auto
# from typing import Any, Iterable, Tuple, Type
# from data.classes.aanvragen import Aanvraag
# from data.classes.aggregator import Aggregator
# from data.classes.bedrijven import Bedrijf
# from data.classes.files import File, Files
# from data.classes.milestones import Milestone
# from data.classes.studenten import Student
# from data.classes.action_log import ActionLog, ActionLogAggregator
# from data.classes.verslagen import Verslag

# from database.dbConst import EMPTY_ID
# from database.sql_expr import Ops, SQE
# from debug.debug import classname
# from general.deep_attr import deep_attr_main_part, deep_attr_sub_part, get_deep_attr, has_deep_attr
# from database.database import Database
# from database.table_def import TableDefinition
# from general.keys import get_next_key
# from general.log import log_debug


# @dataclass
# class CRUD_AggregatorData:
#     main_table_key: CRUDbase
#     aggregator: Aggregator
#     attribute: str
# DBtype = type[str|int|float]

# @dataclass
# class DetailRec:
#     main_key: int 
#     detail_key: int
# DetailRecs = list[DetailRec]

# AAPAClass = Type[Bedrijf|Student|File|Files|Aanvraag|ActionLog|Verslag|Milestone|DetailRec]
# KeyClass = Type[int|str]
# class CRUD(Enum):
#     INIT = auto()
#     CREATE=auto()
#     READ  =auto()
#     UPDATE=auto()
#     DELETE=auto()

# class CRUDbaseHelper:
#     #helper class to avoid clutter in main class
#     def __init__(self, crud: CRUDbase):
#         self.crud = crud
#     @property
#     def table(self)->TableDefinition:
#         return self.crud.table
#     @property
#     def database(self)->Database:
#         return self.crud.database
#     def get_all_columns(self, include_key = True)->list[str]:
#         return([column.name for column in self.table.columns if include_key or (not column.is_primary())])
#     def get_keys(self)->Iterable[str]:
#         return self.table.keys
#     def __get_column_value(self, aapa_obj: AAPAClass, column_name: str):
#         return self.map_object_to_db(column_name, get_deep_attr(aapa_obj, self.crud._db_map[column_name]['attrib'], '???'))
#     def get_key_values(self, aapa_obj: AAPAClass)->Iterable[DBtype]:
#         return [self.__get_column_value(aapa_obj, key) for key in self.get_keys()]
#     def get_all_values(self, aapa_obj: AAPAClass, include_key = True)->Iterable[DBtype]:
#         return [self.__get_column_value(aapa_obj, column_name) for column_name in self.get_all_columns(include_key=include_key)]
#     def __map_column(self, column_name: str, value, map_name):
#         converter = self.crud._db_map[column_name][map_name]        
#         return converter(value) if converter else value
#     def map_object_to_db(self, column_name: str, value)->DBtype:
#         return self.__map_column(column_name, value, 'obj2db')        
#     def map_db_to_object(self, column_name: str, value):
#         return self.__map_column(column_name, value, 'db2obj')  
#     def find_keys_by_column_values(self, column_names: list[str], values: list[Any], map_values=True)->list[int]:
#         log_debug( f'FKBCV start {column_names}   values: {values}' )
#         where_clause = ' AND '.join(f'({colname}={"?"})' for colname in column_names)
#         sql = f'SELECT {self.table.key} from {self.table.name} WHERE {where_clause}'
#         if map_values:
#             values = [self.map_object_to_db(column_name, value) for column_name,value in zip(column_names,values)]
#         if (rows := self.database._execute_sql_command(sql, values, True)):
#             log_debug( f'FKBCV {len(rows)=}' )
#             result = [row[0] for row in rows]            
#             log_debug( f'FKBCV end 0 {result}' )
#             return result
#         return []
#     def find_by_column_values(self, column_names: list[str], values: list[Any], map_values=True)->AAPAClass|list[AAPAClass]:
#         log_debug( f'FBCV start: {column_names}, {values} ({map_values=})' )
#         if not column_names:
#             return None
#         if keys := self.find_keys_by_column_values(column_names, values, map_values=map_values):
#             log_debug( f'FBCV: {keys}' )
#             if len(keys) > 1:
#                 return [self.crud.read(key) for key in keys]
#             else:
#                 return self.crud.read(keys[0])
#         return []
#     def find(self, aapa_obj: AAPAClass)->AAPAClass:        
#         return self.find_by_column_values(self.get_all_columns(include_key=False), 
#                                             self.get_all_values(aapa_obj, include_key=False), map_values=False)
#     def check_already_there(self, aapa_obj: AAPAClass)->bool:
#         if stored := self.find(aapa_obj):
#             if stored == aapa_obj:
#                 log_debug(f'--- already in database ----')                
#             else:
#                 log_debug(f'--- different in database ----')
#             #find checks without key, so the key could still be EMPTY_ID, make sure aapa_obj receives this change
#             setattr(aapa_obj, self.table.key, getattr(stored, self.table.key))
#             return True
#         return False
#     def read_records(self, key: KeyClass)->type[AAPAClass|list]:
#         return self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.map_object_to_db(self.table.key, key), 
#                                                                                     no_column_ref=self.crud.no_column_ref_for_key))        
#     def get_class_dict(self, row)->Tuple[dict,dict]:
#         class_dict = {self.crud._db_map[column_name]['attrib']: self.map_db_to_object(column_name, row[column_name]) 
#                         for column_name in self.get_all_columns()}
#         new_dict = {}
#         for attr,value in class_dict.items():
#             if has_deep_attr(attr):
#                 new_dict[attr] = {'new_attr': deep_attr_main_part(attr), 'sub_attr': deep_attr_sub_part(attr), 'sub_attr_key': value} 
#         for attr, record in new_dict.items():
#             class_dict[record['new_attr']] = None # first initialize as None
#             del class_dict[attr]                
#         log_debug(f'CLASSDICT:{str(class_dict)}')
#         return class_dict, new_dict
#     def __create_subclass_if_not_exists(self, aapa_obj: AAPAClass, attr: str, sub_crud: CRUDbase)->AAPAClass:
#         sub_object = getattr(aapa_obj, attr)
#         sub_crud.create(sub_object)
#         setattr(aapa_obj, attr, sub_object)
#     def create_subclasses(self, aapa_obj):
#         for attr,crud in self.crud.subclass_CRUDs.items():
#             self.__create_subclass_if_not_exists(aapa_obj, attr, crud)
#             # crud.create(getattr(aapa_obj, attr))            
#     def __get_sub_crud(self, attr: str)->CRUDbase:
#         return self.crud.subclass_CRUDs.get(attr, None)
#     def read_sub_attrib(self, attr: str, sub_key: str)->AAPAClass: 
#         if sub_crud := self.__get_sub_crud(attr):
#             return sub_crud.read(sub_key)
#         return None    
        
# class CRUDbase:    
#     #base class also supporting views for reading (SQLite views only support reading)
#     def __init__(self, database: Database, class_type: AAPAClass, 
#                  table: TableDefinition, subclass_CRUDs:dict[str, AAPAClass]={}, no_column_ref_for_key = False, autoID=False):
#         self.database = database
#         self.table = table
#         self.subclass_CRUDs = subclass_CRUDs
#         self.class_type = class_type
#         self.no_column_ref_for_key = no_column_ref_for_key
#         self.autoID = autoID
#         self.aggregator_CRUD_temp: CRUDbase = None
#         self._helper = CRUDbaseHelper(self)
#         self._db_map = {column_name: {'attrib':column_name, 'obj2db': None, 'db2obj': None} for column_name in self._helper.get_all_columns()}
#         self._post_action(None, CRUD.INIT)
#     def create(self, aapa_obj: AAPAClass):
#         log_debug(f'CRUD({classname(self)}) create {str(aapa_obj)}')
#         if self.subclass_CRUDs:
#             self._helper.create_subclasses(aapa_obj)
#         if self._helper.check_already_there(aapa_obj):
#             return
#         if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
#             setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
#         log_debug(f'columns={self._helper.get_all_columns()}  values={self._helper.get_all_values(aapa_obj)}' )
#         self.database.create_record(self.table, columns=self._helper.get_all_columns(), values=self._helper.get_all_values(aapa_obj)) 
#         if self.aggregator_CRUD_temp:
#             self.aggregator_CRUD_temp.create(aapa_obj)
#         self._post_action(aapa_obj, CRUD.CREATE)
#     def read(self, key: KeyClass, multiple=False)->type[AAPAClass|list]:
#         log_debug(f'CRUD({classname(self)}) read {key}')
#         #NOTE: dit zou niet werken voor superclass vrees ik maar dat is nu niet erg meer
#         #NOTE: dit nog aanpassen aan details, maar misschien hoeft dat niet als er altijd een VIEW is in dat geval?!
#         if rows := self._helper.read_records(key):
#             if multiple:
#                 return rows
#             else:
#                 class_dict, new_dict = self._helper.get_class_dict(rows[0])
#                 result = self.class_type(**class_dict)
#                 if self.subclass_CRUDs:
#                     for attr,new_dict_entry in new_dict.items():                        
#                         setattr(result, new_dict_entry['new_attr'], self._helper.read_sub_attrib(deep_attr_main_part(attr),new_dict_entry['sub_attr_key']))
#                 return self._post_action(result, CRUD.READ)
#         return None 
#     def update(self, aapa_obj: AAPAClass):
#         log_debug(f'CRUD({classname(self)}) update {str(aapa_obj)}')
#         where = None
#         for key,value in zip(self.table.keys, self._helper.get_key_values(aapa_obj)):
#             new_where_part = SQE(key, Ops.EQ, value, no_column_ref=self.no_column_ref_for_key)
#             if where is None:
#                 where = new_where_part
#             else:
#                 where = SQE(where, Ops.AND, new_where_part)
#         self.database.update_record(self.table, columns=self._helper.get_all_columns(include_key=False), 
#                                     values=self._helper.get_all_values(aapa_obj, include_key=False), where=where)
#         self._post_action(aapa_obj, CRUD.UPDATE)
#     def delete(self, value: DBtype):
#         log_debug(f'CRUD({classname(self)}) delete {str(value)}')
#         key = self.table.key
#         attrib = self._db_map[key]['attrib']
#         self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self._helper.map_object_to_db(attrib, value), no_column_ref=self.no_column_ref_for_key))
#     def _pre_action(self, aapa_obj: AAPAClass, crud_action: CRUD)->AAPAClass:
#         # placeholder for possible preprocessing, may modify object
#         pass
#     def _post_action(self, aapa_obj: AAPAClass, crud_action: CRUD)->AAPAClass:
#         # placeholder for possible postprocessing, may modify object
#         return aapa_obj  
#     def find_keys(self, column_names: list[str], values: list[Any])->list[int]:
#         return self._helper.find_keys_by_column_values(column_names, values)
#     def find(self, column_names: list[str], values: list[Any])->AAPAClass|list[AAPAClass]:
#         return self._helper.find_by_column_values(column_names, values)
    
