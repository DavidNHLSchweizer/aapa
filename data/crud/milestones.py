from dataclasses import dataclass
from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.aapa_database import AanvraagTableDefinition, StudentMilestonesTableDefinition, VerslagTableDefinition
from data.classes.milestones import Milestone, StudentMilestones
from data.classes.studenten import Student
from data.crud.mappers import TimeColumnMapper
from data.crud.crud_base import CRUD, AAPAClass, CRUDColumnMapper, CRUDbase
from data.crud.crud_factory import createCRUD
from database.database import Database
from database.table_def import TableDefinition

class CRUD_milestones(CRUDbase):
    # semi-abstract base class for AANVRAGEN and VERSLAGEN, handles the common parts
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, 
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def _post_action(self, aapa_obj: AAPAClass, action: CRUD)->AAPAClass:
        match action:
            case CRUD.INIT:
                self.set_mapper(TimeColumnMapper('datum'))
                self.set_mapper(CRUDColumnMapper('stud_id', attribute_name='student', crud=createCRUD(self.database, Student)))
                self.set_mapper(CRUDColumnMapper('bedrijf_id', attribute_name='bedrijf', crud=createCRUD(self.database, Bedrijf)))
            case _: pass
        return aapa_obj

class CRUD_student_milestones(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentMilestonesTableDefinition(), class_type=StudentMilestones, autoID=True)

@dataclass
class MilestoneDetailRelationRec:
    ms_id: int 
    rel_id: int
    rel_type: int

MilestoneDetailRelationRecs = list[MilestoneDetailRelationRec]

class CRUD_milestones_details(CRUDbase):
    def __init__(self, database: Database, relation_table: TableDefinition):
        super().__init__(database, relation_table, None)
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        return None #implement in descendants
    def get_relation_records(self, milestones: StudentMilestones)->MilestoneDetailRelationRecs:
        return [MilestoneDetailRelationRec(milestones.id, object.id, object.milestone_type) 
                for object in sorted(self._get_objects(milestones), key=lambda o: o.id)]
                #gesorteerd om dat het anders - misschien - in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, milestones: StudentMilestones):
        for record in self.get_relation_records(milestones):
            self.database.create_record(self.table, 
                                        columns=self._helper.get_all_columns(), 
                                        values=[record.ms_id, record.rel_id, record.rel_type])   
    # def read(self, milestones_id: int)->MilestoneDetailRelationRecs:
    #     result = []
    #     if rows:=super().read(milestones_id, multiple=True):
    #         for row in rows:
    #             result.append(ActionLogRelationRec(log_id=action_log_id, rel_id=row[self._get_relation_column_name()]))
    #     return result


class CRUD_milestone_details_aanvragen(CRUD_milestones_details):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition())
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        return None #milestones.get({Verslag.Type.AANVRAAG})

class CRUD_milestone_details_verslagen(CRUD_milestones_details):
    def __init__(self, database: Database):
        super().__init__(database, VerslagTableDefinition())
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        # types = {milestone_type for milestone_type in Verslag.Type 
        #             if milestone_type not in {Verslag.Type.UNKNOWN, 
        #                                       Verslag.Type.AANVRAAG}}
        return None
        return milestones.get(types)
