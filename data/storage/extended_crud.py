from data.storage.CRUDs import CRUDColumnMapper, CRUD, CRUDQueries
from data.storage.detail_rec_crud import DetailRecsCRUD
from data.storage.general.storage_const import KeyClass, StorageException, StoredClass
from database.database import Database
from general.classutil import classname

class ExtendedCRUD(CRUD):
    def __init__(self, database: Database, class_type: StoredClass):
        super().__init__(database, class_type)
        self._crud = self.get_crud(class_type) 
        self.details = DetailRecsCRUD(database, class_type) if self._data.details_data else None
    def __check_valid(self, aapa_obj, msg: str):
        if not isinstance(aapa_obj, StoredClass):
            raise StorageException(f'Invalid call to {msg}. {aapa_obj} is not a valid object.')    
    # --------------- CRUD functions ----------------
    def create(self, aapa_obj: StoredClass):
        self.__check_valid(aapa_obj, f"{classname(self)}.create")
        self.create_references(aapa_obj)        
        if CRUDQueries(self).check_already_there(aapa_obj):
            return
        #TODO adapt for multiple keys
        CRUDQueries(self).create_key_if_needed(aapa_obj)
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
    def create_references(self, aapa_obj: StoredClass):
        for mapper in self.mapper.mappers():
            if isinstance(mapper, CRUDColumnMapper):
                CRUDQueries(self).ensure_exists(aapa_obj, mapper.attribute_name, mapper.attribute_key)
  
