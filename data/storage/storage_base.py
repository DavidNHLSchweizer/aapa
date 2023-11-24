from pydoc import classname
from typing import Any
from data.storage.storage_const import AAPAClass, DBtype, KeyClass
from data.storage.table_registry import class_data
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QueryBuilder
from data.storage.storage_crud import StorageCRUD
from database.database import Database
from database.dbConst import EMPTY_ID
from database.table_def import TableDefinition
from general.keys import get_next_key
from general.log import log_debug

class StorageException(Exception): pass

class CRUDColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str, crud: StorageCRUD, attribute_key:str='id'):
        super().__init__(column_name=column_name, attribute_name=attribute_name)
        self.crud = crud
        self.attribute_key = attribute_key
    def map_value_to_db(self, value: AAPAClass)->DBtype:
        return getattr(value, self.attribute_key, None)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return self.crud.read(db_value)

class StorageBase:
    def __init__(self, database: Database, class_type: AAPAClass, autoID=False):
        self.database = database
        self.autoID = autoID
        # self.aggregator_CRUD_temp: CRUDbase = None
        data = class_data(class_type)
        self.mapper = data.mapper_type(database, data.table, class_type) if data.mapper_type else TableMapper(database, data.table, class_type) 
        self._cruds: list[StorageCRUD] = [StorageCRUD(database, class_type)] 
        # list of associated cruds. 
        # _cruds[0] is always the main CRUD (for class_type)
        # other cruds are created as needed (for e.g. associated class types such as Milestone.student)
    @property
    def crud(self)->StorageCRUD:
        return self._cruds[0]
    def get_crud(self, aapa_obj: AAPAClass)->StorageCRUD:
        #create new crud if needed
        for crud in self._cruds:
            if isinstance(aapa_obj, crud.class_type):
                return crud
        self._cruds.append(StorageCRUD(self.database, type(aapa_obj)))
        return self._cruds[-1]
    @property
    def query_builder(self)->QueryBuilder:
        return self.crud.query_builder
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    def customize_mapper(self, mapper: TableMapper):
        pass #for non-standard column mappers, define this in subclass
  
    # --------------- CRUD functions ----------------
    def create(self, aapa_obj: AAPAClass):
        self.__create_references(aapa_obj)        
        if self.__check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        self.__create_key_if_needed(aapa_obj, self.table, self.autoID)
        self.crud.create(aapa_obj)
    @staticmethod #TODO remove duplication with StorageCRUD
    def __create_key_if_needed(aapa_obj: AAPAClass, table: TableDefinition, autoID=False):
        if autoID and getattr(aapa_obj, table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, table.key, get_next_key(table.name))
    def read(self, key: KeyClass, multiple=False)->AAPAClass|list:
        return self.crud.read(key, multiple=multiple)        
    def update(self, aapa_obj: AAPAClass):
        self.__create_references(aapa_obj)
        self.crud.update(aapa_obj)
    def delete(self, aapa_obj: AAPAClass):
        self.crud.delete(aapa_obj)
    def __create_references(self, aapa_obj: AAPAClass):
        for mapper in self.mapper.mappers():
            if isinstance(mapper, CRUDColumnMapper):
                self.__ensure_exists(aapa_obj, mapper.attribute_name, mapper.attribute_key)
    def __ensure_exists(self, aapa_obj: AAPAClass, attribute: str, attribute_key: str = 'id'):
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            return
        crud = self.get_crud(attr_obj)
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_id := crud.query_builder.find_id_from_object(attr_obj):
                setattr(attr_obj, attribute_key, stored_id)
            else:
                self.__create_key_if_needed(attr_obj, crud.table, crud.autoID)
                crud.create(attr_obj)
    def __check_already_there(self, aapa_obj: AAPAClass)->bool:
        if stored_id := self.query_builder.find_id_from_object(aapa_obj): 
            log_debug(f'--- already in database ----')                
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, stored_id)
            return True
        return False
    # utility functions
    def find_value(self, attribute_name: str, value: Any|set[Any])->AAPAClass:
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
