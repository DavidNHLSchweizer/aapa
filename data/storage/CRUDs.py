from __future__ import annotations
from enum import Enum, auto
from typing import Any, Tuple, Type
from data.classes.aapa_class import AAPAclass
from data.classes.detail_rec import DetailRecData
from data.storage.general.mappers import ColumnMapper, TableMapper
from data.storage.general.query_builder import QIF, QueryBuilder
from data.storage.general.storage_const import DBtype, KeyClass, StorageException, StoredClass
from database.database import Database
from database.dbConst import EMPTY_ID
from database.sql_expr import SQE, Ops
from database.table_def import TableDefinition
from general.classutil import classmodule, classname
from general.keys import get_next_key
from general.log import log_debug
from general.singleton import Singleton

class CRUDs(dict):
    # override in subclasses to handle more complicated cases
    # any cruds are created as needed 
    # (for e.g. associated class types such as Milestone.student, or detail tables)
    def __init__(self, database: Database):
        self.database=database
    def get_crud(self, class_type: StoredClass)->CRUD:
        if not (crud := self.get(class_type, None)):
            crud = create_crud(self.database, class_type)
        self[class_type] = crud
        return crud

class CRUD:
    """
        Basic CRUD functions to connect a class to the database
        The standard CRUD class assumes the class corresponds to one table. 
        Subclasses can handle more complicated cases.

        public attributes:
            database: the database
            class_type: associated class type
            
            autoID: whether the associated class uses AAPA-generated keys for the table
                (most classes do this, mostly because it guarantees that higher ID means later 
                creation, SQLite does not guarantee this)
            mapper: the TableMapper mapping object values to the table
            queries: the CRUDQueries object: functions to query the table
            table: the TableDefinition

        public methods:
            --- basic CRUD functions (subclasses can overload to define more complicated behaviours ---
            create(StoredClass): create a new object in the database
            read(Key): read a object from the database
            update(StoredClass): update the object values in the database
            delete(StoredClass): delete the object from the database            

            get_crud: access to associated cruds 

        protected attributes:
            _data: the registered CRUD class data (see register_crud)
            _cruds: the cruds to connect possible associated classes
        
        
    """
#----------- basic CRUD functions, working on one single table --------------
    def __init__(self, database: Database, class_type: StoredClass):
        self._data = _class_data(class_type)
        self.database = database        
        self.autoID = self._data.autoID
        self.mapper = self._data.mapper_type(database, self._data.table, class_type) if self._data.mapper_type \
                                                            else TableMapper(database, self._data.table, class_type)
        self.queries = self._data.queries_type(self)
        self._cruds = CRUDs(database)
    @property
    def table(self)->TableDefinition:
        return self.mapper.table
    @property
    def class_type(self)->StoredClass:
        return self.mapper.class_type   
    @property
    def query_builder(self)->QueryBuilder:
        return self.queries.query_builder
    def get_crud(self, class_type = None)->CRUD:
        return self if not class_type or class_type == self.class_type else self._cruds.get_crud(class_type)
    def create(self, aapa_obj: StoredClass): 
        log_debug(f'CRUD CREATE ({classname(self)}) {classname(aapa_obj)}: {str(aapa_obj)}')
        columns,values = self.mapper.object_to_db(aapa_obj)
        self.database.create_record(self.table, columns=columns, values=values)
        log_debug(f'END CRUD CREATE')
   
    def read(self, key: KeyClass|list[KeyClass])->StoredClass: 
        log_debug(f'CRUD READ ({classname(self)}|{self.table.name}) {classname(self.class_type)}:{key=}')
        result = None
        #TODO: this could probably somehow be better integrated with queries.find_values_where
        if isinstance(key,list):
            where = self.query_builder.build_where_from_values(column_names=self.table.keys, 
                                                               values=key,flags={QIF.NO_MAP_VALUES})
        else:
            where = SQE(self.table.key, Ops.EQ, self.mapper.value_to_db(key, self.table.key))
        if rows := self.database.read_record(self.table, where=where):
            result = self.mapper.db_to_object(rows[0])
        log_debug(f'END CRUD READ: {str(result)}')
        return result
    def read_many(self, keys:set[KeyClass])->list[StoredClass]: 
        log_debug(f'CRUD READ_MANY ({classname(self)}|{self.table.name}) {classname(self.class_type)}')
        result = None
        #TODO: this could probably somehow be better integrated with queries.find_values_where
        if not isinstance(keys,set):
            raise StorageException(f'invalid call to read_many (must be set)')
        where = self.query_builder.build_where_for_many(column_name=self.table.key, 
                                                               values=keys,flags={QIF.NO_MAP_VALUES})
        result = []
        for row in self.database.read_record(self.table, where=where):
            result.append(self.mapper.db_to_object(row))
        log_debug(f'END CRUD READ_MANY: {str(result)}')
        return result    
    def update(self, aapa_obj: StoredClass): 
        log_debug(f'CRUD UPDATE ({classname(self)}|{self.table.name}) {classname(aapa_obj)}: {str(aapa_obj)}')
        columns,values= self.mapper.object_to_db(aapa_obj,include_key=False)
        #TODO: this could probably somehow be better integrated with queries.find_values_where
        self.database.update_record(self.table, columns=columns, values=values, 
                                            where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))
        log_debug(f'END CRUD UPDATE')
        
    def delete(self, aapa_obj: StoredClass):
        log_debug(f'CRUD DELETE ({classname(self)}|{self.table.name}) {classname(aapa_obj)}: {str(aapa_obj)}')
        #TODO: this could probably somehow be better integrated with queries.find_values_where
        self.database.delete_record(self.table, 
                                    where=self.query_builder.build_where_from_object(aapa_obj, column_names=self.mapper.table_keys()))        
        log_debug(f'END CRUD DELETE')

    # ---------------- utility functions ---------------
class EnsureKeyAction(Enum):
    KEY_CREATED = auto()
    ALREADY_THERE = auto()
    NOTHING = auto()
EnsureKeyResults = set[EnsureKeyAction]

class CRUDQueries:        
    # special class with common queries
    def __init__(self, crud: CRUD):
        self._crud = crud
        self._query_builder = QueryBuilder(self._crud.database, self._crud.mapper)
    def get_crud(self, class_type: StoredClass)->CRUD:
        return self.crud.get_crud(class_type=class_type)
    @property
    def crud(self)->CRUD:
        return self._crud
    @property
    def query_builder(self)->QueryBuilder:
        return self._query_builder
    @property
    def table(self)->TableDefinition:
        return self.crud.table
    def __db_log(self, function: str, params: str=''):
        log_debug(f'CH:{classname(self)}|{classname(self.crud)}: {function}{(" - " + params) if params else ""}')
    #----------- utilituy functions -----------
    def check_already_there(self, aapa_obj: StoredClass)->bool:
        self.__db_log('CHECK_ALREADY_THERE', f'object: {aapa_obj}')
        if stored_ids := self.query_builder.find_ids_from_object(aapa_obj): 
            log_debug(f'\tCAT: --- already in database ----')                
            #TODO adapt for multiple keys
            setattr(aapa_obj, self.table.key, stored_ids[0])
            return True
        log_debug(f'\tCAT: not there')                
        return False
    def create_key_if_needed(self, aapa_obj: StoredClass, table: TableDefinition = None, autoID=True)->bool:
        self.__db_log('CREATE_KEY_IF_NEEDED', f'object: {aapa_obj}  table: {table.name if table else None} {autoID=}')
        autoID = autoID if autoID else self.crud.autoID
        table = table if table else self.table
        if autoID and getattr(aapa_obj, table.key, EMPTY_ID) == EMPTY_ID:
            log_debug(f'\tCKIN: setting key')
            setattr(aapa_obj, table.key, get_next_key(table.name))
            return True
        return False
    def ensure_exists(self, aapa_obj: StoredClass, attribute: str, attribute_key: str = 'id'):
        self.__db_log('ENSURE_EXISTS', f'object: {aapa_obj}  {attribute=}  {attribute_key=}')
        if not (attr_obj := getattr(aapa_obj, attribute, None)):
            log_debug(f'\tEE: attribute object not found')
            return
        crud = self.get_crud(type(attr_obj))
        if getattr(attr_obj, attribute_key) == EMPTY_ID:
            if stored_ids := crud.query_builder.find_ids_from_object(attr_obj):
                setattr(attr_obj, attribute_key, stored_ids[0])
                log_debug(f'\tEE: found stored')
            else:
                self.create_key_if_needed(attr_obj, crud.table, crud.autoID)
                crud.create(attr_obj)
                log_debug(f'\tEE: created new')
        else:
            # key already set elsewhere, check whether already in database
            if not (stored_ids := crud.query_builder.find_ids_from_object(attr_obj)):
                log_debug(f'\tEE: not stored: creating new')
                crud.create(attr_obj)
        self.__db_log('END ENSURE_EXISTS')
    def ensure_key(self, aapa_obj: StoredClass)->EnsureKeyAction:
        if self.check_already_there(aapa_obj):
            return EnsureKeyAction.ALREADY_THERE
        if self.create_key_if_needed(aapa_obj):
            return EnsureKeyAction.KEY_CREATED
        else:
            return EnsureKeyAction.NOTHING

    # -------------- searching functions -------------
    def __get_wanted_values(self, attributes: str|list[str], values: Any|list[Any])->Tuple[list[str],list[str]]:
        wanted_attributes = attributes if isinstance(attributes, list) else [attributes]
        wanted_values = values if isinstance(values, list) else [values]
        return (wanted_attributes, wanted_values)
    def find_count(self, attributes: str|list[str]=None, values: Any|list[Any]=None)->int:
        self.__db_log('FIND_COUNT', f'attributes: {attributes} values: {values}')
        qb = self.query_builder
        wanted_attributes, wanted_values = self.__get_wanted_values(attributes, values) 
        log_debug(f'\tFC: {wanted_attributes=} {wanted_values=}')
        return qb.find_count(
                    where=qb.build_where_from_values(
                        column_names=wanted_attributes, values=wanted_values,
                            flags={QIF.ATTRIBUTES, QIF.NO_MAP_VALUES}))        
    def find_max_value(self, attribute: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None)->Any:
        self.__db_log('FIND_MAX_VALUE', f'attribute: {attribute}  where_attributes: {where_attributes} where_values: {where_values}')
        qb = self.query_builder
        wanted_attributes, wanted_values = self.__get_wanted_values(where_attributes, where_values) 
        log_debug(f'\tFMV: {wanted_attributes=} {wanted_values=}')
        if wanted_attributes:
            where = qb.build_where_from_values(
                        column_names=wanted_attributes, values=wanted_values,
                            flags={QIF.ATTRIBUTES, QIF.NO_MAP_VALUES})     
        else:
            where = None   
        return qb.find_max_value(attribute, where= where)
    def find_values(self, attributes: str|list[str], values: Any|list[Any], map_values = True, read_many=False)->list[AAPAclass]:
        self.__db_log('FIND_VALUES', f'attributes: {attributes} values: {values}')
        qb = self.query_builder
        wanted_attributes, wanted_values = self.__get_wanted_values(attributes, values) 
        log_debug(f'\tFV: {wanted_attributes=} {wanted_values=}')
        if (ids := qb.find_ids_from_values(attributes=wanted_attributes, values=wanted_values, 
                        flags={QIF.ATTRIBUTES} if map_values else {QIF.ATTRIBUTES, QIF.NO_MAP_VALUES})):
            if read_many:
                return self.crud.read_many(set(ids))
            else:
                return [self.crud.read(id) for id in ids]
        log_debug(f'\tFV: no values found')
        return []
    def find_values_where(self, attribute: str, where_attributes: str|list[str]=None, where_values: Any|list[Any]=None)->list[Any]:
        self.__db_log('FIND_VALUES_WHERE', f'attribute: {attribute}  where_attributes: {where_attributes} where_values: {where_values}')
        qb = self.query_builder
        wanted_attributes, wanted_values = self.__get_wanted_values(where_attributes, where_values) 
        log_debug(f'\tFVW: {wanted_attributes=} {wanted_values=}')
        return qb.find_all([attribute],
                    where=qb.build_where_from_values(
                        column_names=wanted_attributes, values=wanted_values,
                            flags={QIF.ATTRIBUTES, QIF.NO_MAP_VALUES}))        
    def find_max_id(self)->int:
        return self.query_builder.find_max_id()    
    
class CRUDColumnMapper(ColumnMapper):
    def __init__(self, column_name: str, attribute_name:str, crud: CRUD, attribute_key:str='id'):
        super().__init__(column_name=column_name, attribute_name=attribute_name)
        self.crud = crud
        self.attribute_key = attribute_key
    def map_value_to_db(self, value: StoredClass)->DBtype:
        return getattr(value, self.attribute_key, None)
    def map_db_to_value(self, db_value: DBtype)->Any:
        return self.crud.read(db_value)
    
#----------------------- REGISTRY stuff ----------------
# enabling initialization of crud from given ClassType
#-------------------------------------------------------
class ClassRegistryException(Exception): pass
class ClassRegistryData:
    def __init__(self, table: TableDefinition,
                        mapper_type = TableMapper, 
                        crud=CRUD,  
                        queries_type = CRUDQueries,
                        details_data:list[DetailRecData]=None,
                        autoID=True,
                        module_name=''):
        self.table = table
        self.mapper_type = mapper_type
        self.crud = crud
        self.queries_type = queries_type
        self.details_data = details_data
        self.autoID = autoID
        self.module_name = module_name

class CRUDRegistry(Singleton):
    def __init__(self):
        self._registered_data = {}
    def __check_valid(self, class_type: StoredClass, expect_registered=False)->None:
        if isinstance(class_type, StoredClass):
            raise ClassRegistryException(f'{class_type} is an instance. Only types can be registered.')
        if not issubclass(class_type, StoredClass):
            raise ClassRegistryException(f'Unexpected {class_type} can not be registered.')
        if not expect_registered and self._is_registered(class_type):
            raise ClassRegistryException(f'Class type {classname(class_type)} already registered.')
        elif expect_registered and not self._is_registered(class_type):
            raise ClassRegistryException(f'Class type {class_type} is not registered.')        
    def register(self, class_type:StoredClass, 
                        table: TableDefinition, 
                        mapper_type=TableMapper, 
                        crud=CRUD,  
                        queries_type = CRUDQueries,
                        details_data: list[DetailRecData] = None, 
                        autoID=True, 
                        main=True):
        self.__check_valid(class_type, False)
        module_name = classmodule(class_type).replace('data.classes','data.storage.classes') if main else ''            
        self._registered_data[class_type] = ClassRegistryData(table=table,                                                                
                                                              mapper_type = mapper_type, 
                                                              crud=crud,  
                                                              queries_type = queries_type,
                                                              details_data=details_data,
                                                              autoID=autoID,
                                                              module_name=module_name)
    def _is_registered(self, class_type: StoredClass)->bool:
        return class_type in self._registered_data.keys()
    def class_data(self, class_type: StoredClass)->ClassRegistryData:
        self.__check_valid(class_type, True)      
        return self._registered_data[class_type]
    def get_registered_type(self, module_name: str)->StoredClass:
        for class_type,reg_data in self._registered_data.items():
            if reg_data.module_name == module_name:
                return class_type
        return None
_crud_registry = CRUDRegistry()

def create_crud(database: Database, class_type: StoredClass)->CRUD:
    return _class_data(class_type).crud(database, class_type)

def _class_data(class_type: Type[StoredClass])->ClassRegistryData:
    return _crud_registry.class_data(class_type)
def get_registered_type(module_name: str)->StoredClass:
    return _crud_registry.get_registered_type(module_name)
def register_crud(class_type: Type[StoredClass], 
                  table: TableDefinition, 
                  mapper_type: Type[TableMapper] = TableMapper, 
                  crud = CRUD, 
                  queries_type = CRUDQueries,
                  details_data: list[DetailRecData] = None, 
                  autoID=True, 
                  main=True):
    _crud_registry.register(class_type, 
                            table=table, 
                            mapper_type=mapper_type, 
                            crud=crud, 
                            queries_type=queries_type,
                            details_data=details_data,  
                            autoID=autoID,
                            main=main)
    