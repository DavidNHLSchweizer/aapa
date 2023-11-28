from __future__ import annotations
from abc import abstractmethod
from data.storage.mappers import TableMapper
from data.storage.query_builder import QueryBuilder
from data.storage.storage_const import KeyClass, StoredClass
from data.storage.table_registry import class_data
from database.database import Database
from database.table_def import TableDefinition
      
# class CRUDs(dict):
#     # utility class to access one or more associated cruds
#     # any cruds are created as needed 
#     # (for e.g. associated class types such as Milestone.student, or detail tables)
#     def __init__(self, database: Database, class_type: StoredClass):
#         self.database=database
#         self[class_type] = createCRUD(database, class_type)
#     def get_crud(self, class_type: StoredClass)->CRUD:
#         if not (crud := self.get(class_type, None)):
#             crud = createCRUD(self.database, class_type)
#         self[class_type] = crud
#         return crud

# class CRUD:
#     def __init__(self, database: Database, class_type: StoredClass):
#         self.data = class_data(class_type)
#         self.database = database        
#         self.autoID = self.data.autoID
#         self.mapper = self.data.mapper_type(database, self.data.table, class_type) if self.data.mapper_type \
#                                                             else TableMapper(database, self.data.table, class_type)
#         self.query_builder = QueryBuilder(self.database, self.mapper)
#         # self.cruds = CRUDs(database, class_type)
#     @property
#     def table(self)->TableDefinition:
#         return self.mapper.table
#     @property
#     def class_type(self)->StoredClass:
#         return self.mapper.class_type   
#     @abstractmethod
#     def create(self, aapa_obj: StoredClass): pass
#     @abstractmethod
#     def read(self, key: KeyClass|list[KeyClass])->StoredClass: pass
#     @abstractmethod
#     def update(self, aapa_obj: StoredClass): pass
#     @abstractmethod
#     def delete(self, aapa_obj: StoredClass): pass
