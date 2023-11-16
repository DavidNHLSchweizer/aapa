from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Iterable, Tuple
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.classes.action_log import ActionLog
from data.classes.verslagen import Verslag
from database.dbConst import EMPTY_ID
from database.sql_expr import Ops, SQE
from debug.debug import classname
from general.deep_attr import deep_attr_main_part, deep_attr_sub_part, get_deep_attr, has_deep_attr
from database.database import Database
from database.table_def import TableDefinition
from general.keys import get_next_key
from general.log import log_debug

DBtype = type[str|int|float]
AAPAClass = type[Bedrijf|Student|File|Files|Aanvraag|ActionLog|Verslag|Milestone]
KeyClass = type[int|str]
class CRUD(Enum):
    CREATE=auto()
    READ  =auto()
    UPDATE=auto()
    DELETE=auto()

class CRUDbase:    
    #base class also supporting views for reading (SQLite views only support reading)
    def __init__(self, database: Database, class_type: AAPAClass, 
                 table: TableDefinition, 
                    subclass_CRUDs:dict[str, AAPAClass]={}, no_column_ref_for_key = False, autoID=False):
        self.database = database
        self.table = table
        self.subclass_CRUDs = subclass_CRUDs
        self._db_map = {column_name: {'attrib':column_name, 'obj2db': None, 'db2obj': None} for column_name in self._get_all_columns()}
        self.class_type = class_type
        self.no_column_ref_for_key = no_column_ref_for_key
        self.autoID = autoID
        self._after_init()
    def _after_init(self): 
        pass        
    def _get_all_columns(self, include_key = True)->list[str]:
        return([column.name for column in self.table.columns if include_key or (not column.is_primary())])
    def get_keys(self)->Iterable[str]:
        return self.table.keys
    def __get_column_value(self, aapa_obj: AAPAClass, column_name: str):
        return self.map_object_to_db(column_name, get_deep_attr(aapa_obj, self._db_map[column_name]['attrib'], '???'))
    def _get_key_values(self, aapa_obj: AAPAClass)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, key) for key in self.get_keys()]
    def _get_all_values(self, aapa_obj: AAPAClass, include_key = True)->Iterable[DBtype]:
        return [self.__get_column_value(aapa_obj, column_name) for column_name in self._get_all_columns(include_key=include_key)]
    def __map_column(self, column_name: str, value, map_name):
        converter = self._db_map[column_name][map_name]        
        return converter(value) if converter else value
    def map_object_to_db(self, column_name: str, value)->DBtype:
        return self.__map_column(column_name, value, 'obj2db')        
    def map_db_to_object(self, column_name: str, value):
        return self.__map_column(column_name, value, 'db2obj')  
    def __find_by_column_values(self, column_names: list[str], values: list[Any])->AAPAClass|list[AAPAClass]:
        #nog niet helemaal waar het moet zijn
        where_clause = ' AND '.join(f'({colname}={"?"})' for colname in column_names)
        sql = f'SELECT {self.table.key} from {self.table.name} WHERE {where_clause}'
        if (rows := self.database._execute_sql_command(sql, values, True)):
            if len(rows) > 1:
                return [self.read(row[0]) for row in rows]
            else:
                return self.read(rows[0][0])
        return None
    def find(self, aapa_obj: AAPAClass)->AAPAClass:        
        return self.__find_by_column_values(self._get_all_columns(include_key=False), 
                                            self._get_all_values(aapa_obj, include_key=False))
    def __check_already_there(self, aapa_obj: AAPAClass)->bool:
        if stored := self.find(aapa_obj):
            if stored == aapa_obj:
                log_debug(f'--- already in database ----')                
            else:
                log_debug(f'--- different in database ----')
                # self.update(aapa_obj) denk ik niet nodig
            #find checks without key, so the key could still be EMPTY_ID
            setattr(aapa_obj, self.table.key, getattr(stored, self.table.key))
            return True
        return False
    def create(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD({classname(self)}) create {str(aapa_obj)}')
        if self.subclass_CRUDs:
            self.__create_subclasses(aapa_obj)
        if self.__check_already_there(aapa_obj):
            return
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
        self.database.create_record(self.table, columns=self._get_all_columns(), values=self._get_all_values(aapa_obj)) 
    def __create_subclass_if_not_exists(self, aapa_obj: AAPAClass, attr: str, sub_crud: CRUDbase)->AAPAClass:
        sub_object = getattr(aapa_obj, attr)
        sub_crud.create(sub_object)
        setattr(aapa_obj, attr, sub_object)
    def __create_subclasses(self, aapa_obj):
        for attr,crud in self.subclass_CRUDs.items():
            self.__create_subclass_if_not_exists(aapa_obj, attr, crud)
            # crud.create(getattr(aapa_obj, attr))            
    def __get_sub_crud(self, attr: str)->CRUDbase:
        return self.subclass_CRUDs.get(attr, None)
    def _read_sub_attrib(self, attr: str, sub_key: str)->AAPAClass: 
        if sub_crud := self.__get_sub_crud(attr):
            return sub_crud.read(sub_key)
        return None    
    def read_records(self, key: KeyClass)->type[AAPAClass|list]:
        return self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.map_object_to_db(self.table.key, key), 
                                                                                    no_column_ref=self.no_column_ref_for_key))        
    def __get_class_dict(self, row)->Tuple[dict,dict]:
        class_dict = {self._db_map[column_name]['attrib']: self.map_db_to_object(column_name, row[column_name]) 
                        for column_name in self._get_all_columns()}
        new_dict = {}
        for attr,value in class_dict.items():
            if has_deep_attr(attr):
                new_dict[attr] = {'new_attr': deep_attr_main_part(attr), 'sub_attr': deep_attr_sub_part(attr), 'sub_attr_key': value} 
                                #    self._read_sub_attrib(deep_attr_main_part(attr), value)}
        for attr, record in new_dict.items():
            class_dict[record['new_attr']] = None # first initialize as None
            del class_dict[attr]                
        log_debug(f'CLASSDICT:{str(class_dict)}')
        return class_dict, new_dict
    def read(self, key: KeyClass, multiple=False)->type[AAPAClass|list]:
        log_debug(f'CRUD({classname(self)}) read {key}')
        #NOTE: dit zou niet werken voor superclass vrees ik maar dat is nu niet erg meer
        #NOTE: dit nog aanpassen aan details, maar misschien hoeft dat niet als er altijd een VIEW is in dat geval?!
        if rows := self.read_records(key):
            if multiple:
                return rows
            else:
                class_dict, new_dict = self.__get_class_dict(rows[0])
                result = self.class_type(**class_dict)
                if self.subclass_CRUDs:
                    for attr,new_dict_entry in new_dict.items():                        
                        setattr(result, new_dict_entry['new_attr'], self._read_sub_attrib(deep_attr_main_part(attr),new_dict_entry['sub_attr_key']))
                return result
                # return self._post_process(, CRUD.READ)
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
    def delete(self, value: DBtype):
        log_debug(f'CRUD({classname(self)}) delete {str(value)}')
        key = self.table.key
        attrib = self._db_map[key]['attrib']
        self.database.delete_record(self.table, where=SQE(key, Ops.EQ, self.map_object_to_db(attrib, value), no_column_ref=self.no_column_ref_for_key))

    def _pre_process(self, aapa_obj: AAPAClass, action: CRUD)->AAPAClass:
        return aapa_obj # placeholder for possible postprocessing in read objects
    def _post_process(self, aapa_obj: AAPAClass, action: CRUD)->AAPAClass:
        return aapa_obj # placeholder for possible postprocessing in read objects

class CRUDbaseDetails(CRUDbase):pass
# #solution for n-n relation tabel 
#     @dataclass
#     class DetailRec:
#         main_id: int 
#         detail_id: int
#     DetailRecs = list[DetailRec]

#     def __init__(self, CRUD_main: CRUDbase, detail_table: TableDefinition):
#         assert len(detail_table.keys) == 2
#         super().__init__(CRUD_main.database, class_type=None, table=detail_table)
#     def _get_relation_column_name(self)->str:
#         log_debug(f'GRC: {self.table.keys[1]}')
#         return self.table.keys[1]
#     @abstractmethod
#     def _get_objects(self, object: AAPAClass)->Iterable[AAPAClass]:
#         return None #implement in descendants
#     def get_detail_records(self, main: AAPAClass)->DetailRecs:
#         return [CRUDbaseDetails.DetailRec(main.id, detail.id) 
#                 for detail in sorted(self._get_objects(main), key=lambda d: d.id)]
#                 #gesorteerd om dat het anders in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
#     def read(self, main_id: int)->DetailRecs:
#         result = []
#         if rows:=super().read(main_id, multiple=True):
#             for row in rows:
#                 result.append(CRUDbaseDetails.DetailRec(main_id=main_id, detail_id=row[self._get_relation_column_name()]))
#         return result
#     def update(self, main: AAPAClass):
#         def is_changed()->bool:
#             new_records = self.get_detail_records(main)
#             current_records= self.read(main.id)
#             if len(new_records) != len(current_records):
#                 return True
#             else:
#                 for new, current in zip(new_records, current_records):
#                     if new != current:
#                         return True
#             return False
#         if is_changed():
#             self._update(main)
#     def _update(self, main: AAPAClass):        
#         self.delete(main.id)    
#         self.create(main)
#     def delete_relation(self, detail_id: int):
#         self.database._execute_sql_command(f'delete from {self.table.name} where {self._get_relation_column_name()}=?', [detail_id])        

