from data.general.aggregator import Aggregator
from storage.general.CRUDs import CRUDColumnMapper, CRUD, CRUDQueries
from storage.general.details_crud import DetailsCRUD
from storage.general.storage_const import KeyClass, StorageException, StoredClass
from database.classes.database import Database
from general.classutil import classname
from main.log import log_debug

class AggregatorCRUD(CRUD):
    """ CRUD with automatic support for detail tables (Aggregator objects) """
    def __init__(self, database: Database, class_type: StoredClass):
        super().__init__(database, class_type)
        self.details = DetailsCRUD(database, class_type) if self._data.details_record_type else None
    def __check_valid(self, aapa_obj, msg: str):
        if not isinstance(aapa_obj, StoredClass):
            raise StorageException(f'Invalid call to {msg}. {aapa_obj} is not a valid object.')  
    # --------------- CRUD functions ----------------
    def __db_log(self, function: str, params: str=''):
        log_debug(f'EXT-CRUD({classname(self)}): {function}{(" - " + params) if params else ""}') 
    def _create_new(self, aapa_obj):
        CRUDQueries(self).create_key_if_needed(aapa_obj)
        super().create(aapa_obj)
        if self.details:
            self.details.create(aapa_obj)
    def create(self, aapa_obj: StoredClass):
        self.__db_log('CREATE', f'[{classname(aapa_obj)}]')
        self.__check_valid(aapa_obj, f"{classname(self)}.create")
        self.create_references(aapa_obj) 
        already_there = CRUDQueries(self).check_already_there(aapa_obj)
        if already_there:
            if CRUDQueries(self).is_changed(aapa_obj):
                log_debug(f'Updating {aapa_obj}')
                self.update(aapa_obj)
        else:
            log_debug(f'Creating new {aapa_obj}')
            self._create_new(aapa_obj)
        self.__db_log('END CREATE')
    def read(self, key: KeyClass)->StoredClass|list:
        self.__db_log('READ', f'[{key}]')
        result = super().read(key)        
        if result and self.details:
            self.details.read(result)
        self.__db_log('END READ', f'{result}')
        return result
    def read_many(self, keys: set[KeyClass])->StoredClass|list:
        self.__db_log('READ MANY', f'[{keys}]')
        for result in (results := super().read_many(keys)):
            if result and self.details:
                self.details.read(result)
        self.__db_log('END READ MANY', f'{results}')
        return results
    def update(self, aapa_obj: StoredClass):
        self.__db_log('UPDATE', f'[{classname(aapa_obj)}]')
        self.__check_valid(aapa_obj, f"{classname(self)}.update")
        self.create_references(aapa_obj)
        super().update(aapa_obj)
        if self.details:
            self.details.update(aapa_obj)
        self.__db_log('END UPDATE')
    def delete(self, aapa_obj: StoredClass):
        self.__db_log('DELETE', f'[{classname(aapa_obj)}]')
        self.__check_valid(aapa_obj, f"{classname(self)}.delete")
        if self.details:
            self.details.delete(aapa_obj)
        super().delete(aapa_obj)
        self.__db_log('END DELETE')
    # utility functions
    def create_references(self, aapa_obj: StoredClass):
        for mapper in self.mapper.mappers():
            if isinstance(mapper, CRUDColumnMapper):
                CRUDQueries(self).ensure_exists(aapa_obj, mapper.attribute_name, mapper.attribute_key)
  
