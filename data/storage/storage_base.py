from pydoc import classname
from typing import Any
from data.crud.crud_const import AAPAClass, DBtype, KeyClass
from data.crud.crud_factory import createCRUD
from data.crud.mappers import ColumnMapper, TableMapper
from data.crud.query_builder import QueryBuilder
from database.database import Database
from database.dbConst import EMPTY_ID
from database.sql_expr import SQE, Ops
from database.table_def import TableDefinition
from general.keys import get_next_key
from general.log import log_debug


class StorageException(Exception): pass

class StorageCRUD:
    def __init__(self, database: Database, mapper: TableMapper, autoID=False):
        self.database = database
        self.autoID = autoID
        self.mapper = mapper
        self.searcher = QueryBuilder(self.database, self.mapper)
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    def create(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD CREATE ({classname(self)}) {str(aapa_obj)}')
        columns,values = self.mapper.object_to_db(aapa_obj)
        self.database.create_record(self.table, columns=columns, values=values)
    def read(self, key: KeyClass, multiple=False)->AAPAClass|list:
        log_debug(f'CRUD READ ({classname(self)}) {key}')
        if rows := self.database.read_record(self.table, where=SQE(self.table.key, Ops.EQ, self.mapper.value_to_db(key, self.table.key))):
            if multiple:
                return rows #deal with this later!
            else:
                return self.mapper.db_to_object(rows[0])
        return None 
    def update(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD UPDATE ({classname(self)}) {str(aapa_obj)}')
        columns,values= self.mapper.object_to_db(aapa_obj,include_key=False)
        self.database.update_record(self.table, columns=columns, values=values, 
                                            where=self.searcher.build_where(aapa_obj, column_names=self.mapper.table_keys()))
    def delete(self, aapa_obj: AAPAClass):
        log_debug(f'CRUD DELETE ({classname(self)}) {str(aapa_obj)}')
        self.database.delete_record(self.table, 
                                    where=self.searcher.build_where(aapa_obj, column_names=self.mapper.table_keys()))        

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
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, autoID=False):
        self.database = database
        self.autoID = autoID
        # self.aggregator_CRUD_temp: CRUDbase = None
        self.mapper = TableMapper(table, class_type)
        self.customize_mapper()
        self.searcher = QueryBuilder(self.database, self.mapper)
        self._cruds: list[StorageBase] = [StorageCRUD(database, self.mapper, autoID=autoID)]
            
            # createCRUD(database, class_type)]
    @property
    def crud(self)->StorageCRUD:
        return self._cruds[0]
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    @property
    def class_type(self)->AAPAClass:
        return self.mapper.class_type
    def customize_mapper(self):
        pass #for non-standard column mappers
    def set_mapper(self, column_mapper: ColumnMapper):
        self.mapper.set_mapper(column_mapper)


    # def _get_crud(self, aapa_obj: AAPAClass)->CRUDbase:
    #     for crud in self._cruds:
    #         if isinstance(aapa_obj, crud.class_type):
    #             return crud
    #     self._cruds.append(createCRUD(self.database, type(aapa_obj)))
    #     return self._cruds[-1]

    # --------------- CRUD functions ----------------
    def create(self, aapa_obj: AAPAClass):
        self.create_references(aapa_obj)        
        if self.check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        if self.autoID and getattr(aapa_obj, self.table.key, EMPTY_ID) == EMPTY_ID:
            setattr(aapa_obj, self.table.key, get_next_key(self.table.name))
        self.crud.create(aapa_obj)
    def read(self, key: KeyClass, multiple=False)->AAPAClass|list:
        return self.crud.read(key, multiple=multiple)        
    def update(self, aapa_obj: AAPAClass):
        self.create_references(aapa_obj)
        self.crud.update(aapa_obj)
    def delete(self, aapa_obj: AAPAClass):
        self.crud.delete(aapa_obj)
    def create_references(self, aapa_obj: AAPAClass):
        if (references := self._table_mappers())
        # implement this in subclasses to ensure any class-level attributes in the object
        # exist in the database before the object is created
        pass #implement in subclasses as needed
    def ensure_exists(self, aapa_obj: AAPAClass, attribute: str, attribute_key: str = 'id'):
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            return
        crud = self._get_crud(attr_obj)
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_id := crud.find_id(attr_obj):
                setattr(attr_obj, attribute_key, stored_id)
            else:
                crud.create(attr_obj)
    def check_already_there(self, aapa_obj: AAPAClass)->bool:
        if stored_id := self.searcher.find_id(aapa_obj): 
            log_debug(f'--- already in database ----')                
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, stored_id)
            return True
        return False

    def __get_CRUD_column_mappers(self)->list[CRUDColumnMapper]:
        return []
    CRUDColumnMapper

    def find_keys(self, column_names: list[str], values: list[Any])->list[int]:
        return []# self.crud.find_keys(column_names, values) TBD
    def find(self, column_names: list[str], column_values: list[Any])->AAPAClass|list[AAPAClass]:
        return self.crud.find_from_values(column_names=column_names, attribute_values=column_values)
    @property
    def table_name(self)->str:
        return self.crud.table.name
    def max_id(self):
        if (row := self.database._execute_sql_command(f'select max(id) from {self.table_name}', [], True)) and row[0][0]:
            return row[0][0]           
        else:
            return 0                    
    def read_all(self)->Iterable[AAPAClass]:
        if (rows := self.database._execute_sql_command(f'select id from {self.table_name}', [],True)):
            return [self.crud.read(row['id']) for row in rows] 
        return []  
