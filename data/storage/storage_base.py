from typing import Any
from data.classes.aapa_class import AAPAclass
from data.classes.detail_rec import DetailRec
from data.storage.detail_rec import DetailRecStorage
from data.storage.simple_crud import CRUDColumnMapper, SimpleCRUD
from data.storage.storage_const import StorageException, StoredClass, DBtype,KeyClass
from data.storage.table_registry import _class_data
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QueryBuilder
from database.database import Database
from database.dbConst import EMPTY_ID
from database.table_def import TableDefinition
from general.classutil import classname
from general.keys import get_next_key
from general.log import log_debug

class StorageBase(SimpleCRUD):
    def __init__(self, database: Database, class_type: StoredClass):
        super().__init__(database, class_type)
        self._crud = self.get_crud(class_type) 
        self.details = DetailRecStorage(database, class_type) if self.data.details_data else None
    def __check_valid(self, aapa_obj, msg: str):
        if not isinstance(aapa_obj, StoredClass):
            raise StorageException(f'Invalid call to {msg}. {aapa_obj} is not a valid object.')
    # def _create_key_if_needed(self, aapa_obj: StoredClass):
    #     if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
    #         setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
    # def ensure_key(self, aapa_obj: StoredClass):
    #     if not self._check_already_there(aapa_obj):
    #         self._create_key_if_needed(aapa_obj)
    #     self.database.commit()
    def __ensure_exists(self, aapa_obj: StoredClass, attribute: str, attribute_key: str = 'id'):
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            return
        crud = self.get_crud(type(attr_obj))
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_ids := crud.query_builder.find_id_from_object(attr_obj):
                setattr(attr_obj, attribute_key, stored_ids[0])
            else:
                self._create_key_if_needed(attr_obj, crud.table, crud.autoID)
                crud.create(attr_obj)
        else:
            # key already set elsewhere, could not yet be in database
            if not (stored_ids := crud.query_builder.find_id_from_object(attr_obj)):
                crud.create(attr_obj)

    # --------------- CRUD functions ----------------
    def create(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.create")
        self.__create_references(aapa_obj)        
        if self._check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        self.__create_key_if_needed(aapa_obj, self.table, self.autoID)
        super().create(aapa_obj)
        if self.details:
            self.details.create(aapa_obj)
    @staticmethod #TODO remove duplication with StorageCRUD
    def __create_key_if_needed(aapa_obj: StoredClass, table: TableDefinition, autoID=False):
        if autoID and getattr(aapa_obj, table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, table.key, get_next_key(table.name))
    def read(self, key: KeyClass)->StoredClass|list:
        result = super().read(key)        
        if result and self.details:
            self.details.read(result)
        return result
    def update(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.update")
        self.__create_references(aapa_obj)
        super().update(aapa_obj)
        if self.details:
            self.details.update(aapa_obj)
    def delete(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.delete")
        if self.details:
            self.details.delete(aapa_obj)
        super().delete(aapa_obj)
    def __create_references(self, aapa_obj: StoredClass):
        for mapper in self.mapper.mappers():
            if isinstance(mapper, CRUDColumnMapper):
                self.__ensure_exists(aapa_obj, mapper.attribute_name, mapper.attribute_key)
    def __ensure_exists(self, aapa_obj: StoredClass, attribute: str, attribute_key: str = 'id'):
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            return
        crud = self.get_crud(type(attr_obj))
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_ids := crud.query_builder.find_id_from_object(attr_obj):
                setattr(attr_obj, attribute_key, stored_ids[0])
            else:
                self.__create_key_if_needed(attr_obj, crud.table, crud.autoID)
                crud.create(attr_obj)
        else:
            # key already set elsewhere, could not yet be in database
            if not (stored_ids := crud.query_builder.find_id_from_object(attr_obj)):
                crud.create(attr_obj)

    # utility functions
    def find_value(self, attribute_name: str, value: Any|set[Any])->StoredClass:
        if id := self.query_builder.find_value(attribute_name, value):
            return self.read(id)
        return None
    def max_id(self)->int:
        return self.query_builder.find_max_id()    



    # def find_keys(self, column_names: list[str], values: list[Any])->list[int]:
    #     return []# self.crud.find_keys(column_names, values) TBD
    # def find(self, column_names: list[str], column_values: list[Any])->AAPAClass|list[AAPAClass]:
    #     return self.crud.find_from_values(column_names=column_names, attribute_values=column_values)
    # @property
    # def table_name(self)->str:
    #     return self.crud.table.name
    # def max_id(self):
    #     if (row := self.database._execute_sql_command(f'select max(id) from {self.table_name}', [], True)) and row[0][0]:
    #         return row[0][0]           
    #     else:
    #         return 0                    
    # def read_all(self)->Iterable[AAPAClass]:
    #     if (rows := self.database._execute_sql_command(f'select id from {self.table_name}', [],True)):
    #         return [self.crud.read(row['id']) for row in rows] 
    #     return []  

    # def _check_already_there(self, aapa_obj: StoredClass)->bool:
    #     if stored_ids := self.query_builder.find_id_from_object(aapa_obj): 
    #         log_debug(f'--- already in database ----')                
    #         #TODO adapt for multiple keys
    #         setattr(aapa_obj, self.table.key, stored_ids[0])
    #         return True
    #     return False
