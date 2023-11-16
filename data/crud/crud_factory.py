from typing import Type
from data.crud.crud_base import AAPAClass, CRUDbase
from database.database import Database
from database.table_def import TableDefinition
from debug.debug import classname
from general.singleton import Singleton

class CRUD_factory(Singleton):
    def __init__(self):
        self._registered_CRUDs = {}
    def register(self, CRUDclass: Type[CRUDbase], class_type: AAPAClass, table: TableDefinition, 
                                 subclasses: dict[str, AAPAClass]={},
                                 no_column_ref_for_key = False, autoID=False):
        if self._is_registered(class_type):
            raise TypeError(f'Class type {classname(class_type)} already registered.')
        self._registered_CRUDs[class_type] = {'class': CRUDclass, 'table': table, 
                                              'subclasses': subclasses,
                                              'no_column_ref_for_key': no_column_ref_for_key, 'autoID': autoID}
    def _is_registered(self, class_type: AAPAClass)->bool:
        return class_type in self._registered_CRUDs.keys()
    def __get_sub_cruds(self, database: Database, entry: dict[str,AAPAClass]):
        result = {}
        for attrib,class_type in entry.items():
            result[attrib] = self.create(database, class_type)
        return result
    def create(self, database: Database, class_type: AAPAClass)->CRUDbase:
        if not self._is_registered(class_type):
            return None
        entry = self._registered_CRUDs[class_type]
        return entry['class'](database=database, class_type=class_type, table=entry['table'],  
                             subclass_CRUDs=self.__get_sub_cruds(database, entry['subclasses']),                             
                             no_column_ref_for_key=entry['no_column_ref_for_key'], autoID=entry['autoID'])

_crud_factory = CRUD_factory()

def createCRUD(database: Database, class_type: AAPAClass)->CRUDbase:
    return _crud_factory.create(database, class_type)
def registerCRUD(CRUDclass: Type[CRUDbase], class_type: AAPAClass, table: TableDefinition=None, 
                                subclasses: dict[str, AAPAClass]={}, 
                                 no_column_ref_for_key = False, autoID=False):
    _crud_factory.register(CRUDclass, class_type, table=table, 
                           subclasses=subclasses, no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)