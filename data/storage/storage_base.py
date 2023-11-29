from typing import Any
from data.storage.detail_rec import DetailRecStorage
from data.storage.general.storage_const import KeyClass, StorageException, StoredClass
from data.storage.table_crud import TableCRUD
from database.database import Database
from general.classutil import classname

class StorageBase(TableCRUD):
    def __init__(self, database: Database, class_type: StoredClass):
        super().__init__(database, class_type)
        self._crud = self.get_crud(class_type) 
        self.details = DetailRecStorage(database, class_type) if self.data.details_data else None
    def __check_valid(self, aapa_obj, msg: str):
        if not isinstance(aapa_obj, StoredClass):
            raise StorageException(f'Invalid call to {msg}. {aapa_obj} is not a valid object.')
    
    # --------------- CRUD functions ----------------
    def create(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.create")
        self.create_references(aapa_obj)        
        if self._check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        self._create_key_if_needed(aapa_obj)
        super().create(aapa_obj)
        if self.details:
            self.details.create(aapa_obj)
    def read(self, key: KeyClass)->StoredClass|list:
        result = super().read(key)        
        if result and self.details:
            self.details.read(result)
        return result
    def update(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.update")
        self.create_references(aapa_obj)
        super().update(aapa_obj)
        if self.details:
            self.details.update(aapa_obj)
    def delete(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.delete")
        if self.details:
            self.details.delete(aapa_obj)
        super().delete(aapa_obj)

    # utility functions
    def find_value(self, attribute_name: str, value: Any|set[Any])->StoredClass:
        if ids := self.query_builder.find_value(attribute_name, value):
            return [self.read(id) for id in ids]
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
