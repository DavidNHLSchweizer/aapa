from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.mijlpaal_base import MijlpaalBase
from data.classes.studenten import Student
from data.storage.general.mappers import ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.storage_const import StoredClass
from data.storage.CRUDs import create_crud, CRUDColumnMapper
from database.database import Database

class MijlpaalBaseTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper(column_name, attribute_name='student', crud=create_crud(database, Student))
            case 'bedrijf_id': 
                return CRUDColumnMapper(column_name, attribute_name='bedrijf', crud=create_crud(database, Bedrijf))
            case _: return super()._init_column_mapper(column_name, database)

# class MijlpaalBaseCRUD(ExtendedCRUD):
#     def __init__(self, database: Database, class_type: StoredClass):
#         super().__init__(database, class_type)
#     def __read_all_filtered(self, milestones: Iterable[MijlpaalBase], filter_func = None)->Iterable[MijlpaalBase]:
#         if not filter_func:
#             return milestones
#         else:
#             return list(filter(filter_func, milestones))
#     def __read_all_all(self, filter_func = None)->Iterable[MijlpaalBase]:
#         if ids := self.query_builder.find_ids():
#             return self.__read_all_filtered([self.read(id) for id in ids], filter_func=filter_func)
#         return []
#     def __read_all_states(self, states:set[int], filter_func = None)->Iterable[MijlpaalBase]:
#         if ids:= self.query_builder.find_ids_from_values(['status'], [states]):
#             return self.__read_all_filtered([self.read(id) for id in ids], filter_func=filter_func)
#         return []
#     def read_all(self, filter_func = None, states:set[int]=None)->Iterable[MijlpaalBase]:
#         if not states:
#             return self.__read_all_all(filter_func=filter_func)        
#         else: 
#             return self.__read_all_states(filter_func=filter_func, states=states)
