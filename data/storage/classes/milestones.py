from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.storage.general.mappers import ColumnMapper, TableMapper, TimeColumnMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.storage_const import StoredClass
from data.storage.CRUDs import create_crud, CRUDColumnMapper
from database.database import Database

class MilestonesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper('stud_id', attribute_name='student', crud=create_crud(database, Student))
            case 'bedrijf_id': 
                return CRUDColumnMapper('bedrijf_id', attribute_name='bedrijf', crud=create_crud(database, Bedrijf))
            case _: return super()._init_column_mapper(column_name, database)

class MilestonesCRUD(ExtendedCRUD):
    def __init__(self, database: Database, class_type: StoredClass):
        super().__init__(database, class_type)
    def __read_all_filtered(self, milestones: Iterable[Milestone], filter_func = None)->Iterable[Milestone]:
        if not filter_func:
            return milestones
        else:
            return list(filter(filter_func, milestones))
    def __read_all_all(self, filter_func = None)->Iterable[Milestone]:
        if ids := self.query_builder.find_id():
            return self.__read_all_filtered([self.read(id) for id in ids], filter_func=filter_func)
        return []
    def __read_all_states(self, states:set[int], filter_func = None)->Iterable[Milestone]:
        if ids:= self.query_builder.find_id_from_values(['status'], [states]):
            return self.__read_all_filtered([self.read(id) for id in ids], filter_func=filter_func)
        return []
    def read_all(self, filter_func = None, states:set[int]=None)->Iterable[Milestone]:
        if not states:
            return self.__read_all_all(filter_func=filter_func)        
        else: 
            return self.__read_all_states(filter_func=filter_func, states=states)








# class CRUD_student_milestones(CRUDbase):
#     def __init__(self, database: Database):
#         super().__init__(database, StudentMilestonesTableDefinition(), class_type=StudentMilestones, autoID=True)

# @dataclass
# class MilestoneDetailRelationRec:
#     ms_id: int 
#     rel_id: int
#     rel_type: int

# MilestoneDetailRelationRecs = list[MilestoneDetailRelationRec]

# class CRUD_milestones_details(CRUDbase):
#     def __init__(self, database: Database, relation_table: TableDefinition):
#         super().__init__(database, relation_table, None)
#     def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
#         return None #implement in descendants
#     def get_relation_records(self, milestones: StudentMilestones)->MilestoneDetailRelationRecs:
#         return [MilestoneDetailRelationRec(milestones.id, object.id, object.milestone_type) 
#                 for object in sorted(self._get_objects(milestones), key=lambda o: o.id)]
#                 #gesorteerd om dat het anders - misschien - in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
#     def create(self, milestones: StudentMilestones):
#         for record in self.get_relation_records(milestones):
#             self.database.create_record(self.table, 
#                                         columns=self._helper.get_all_columns(), 
#                                         values=[record.ms_id, record.rel_id, record.rel_type])   
#     # def read(self, milestones_id: int)->MilestoneDetailRelationRecs:
#     #     result = []
#     #     if rows:=super().read(milestones_id, multiple=True):
#     #         for row in rows:
#     #             result.append(ActionLogRelationRec(log_id=action_log_id, rel_id=row[self._get_relation_column_name()]))
#     #     return result


# class CRUD_milestone_details_aanvragen(CRUD_milestones_details):
#     def __init__(self, database: Database):
#         super().__init__(database, AanvraagTableDefinition())
#     def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
#         return None #milestones.get({Verslag.Type.AANVRAAG})

# class CRUD_milestone_details_verslagen(CRUD_milestones_details):
#     def __init__(self, database: Database):
#         super().__init__(database, VerslagTableDefinition())
#     def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
#         # types = {milestone_type for milestone_type in Verslag.Type 
#         #             if milestone_type not in {Verslag.Type.UNKNOWN, 
#         #                                       Verslag.Type.AANVRAAG}}
#         return None
#         return milestones.get(types)
