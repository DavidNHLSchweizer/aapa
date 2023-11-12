from dataclasses import dataclass
from typing import Iterable
from data.AAPdatabase import MilestoneTableDefinition, AanvraagTableDefinition, StudentMilestonesTableDefinition, VerslagTableDefinition
from data.classes.bedrijven import Bedrijf
from data.classes.milestones import Milestone, StudentMilestones
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.crud.crud_base import CRUDbase, CRUDbaseAuto
from data.crud.studenten import CRUD_studenten
from database.database import Database
from database.tabledef import TableDefinition

class CRUD_milestones(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, MilestoneTableDefinition(), None)
        # self._db_map['stud_id']['attrib'] = 'student.id'
        # self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
    def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->Student|Bedrijf:
        if sub_attrib_name == 'id':
            match main_part:
                case 'student': 
                    return CRUD_studenten(self.database).read(value)
                case 'bedrijf': 
                    return CRUD_bedrijven(self.database).read(value)
        return None


class CRUD_student_milestones(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, StudentMilestonesTableDefinition(), StudentMilestones)
        self._db_map['student_id']['attrib'] = 'student.id'
        self._db_map['basedir_id']['attrib'] = 'base_dir.id'

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
                                        columns=self._get_all_columns(), 
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
        return milestones.get({Milestone.Type.AANVRAAG})

class CRUD_milestone_details_verslagen(CRUD_milestones_details):
    def __init__(self, database: Database):
        super().__init__(database, VerslagTableDefinition())
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        types = {milestone_type for milestone_type in Milestone.Type 
                    if milestone_type not in {Milestone.Type.UNKNOWN, 
                                              Milestone.Type.AANVRAAG}}
        return milestones.get(types)
