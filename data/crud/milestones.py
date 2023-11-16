from dataclasses import dataclass
from typing import Iterable
from data.aapa_database import MilestoneTableDefinition, AanvraagTableDefinition, StudentMilestonesTableDefinition, VerslagTableDefinition
from data.classes.bedrijven import Bedrijf
from data.classes.milestones import Milestone, StudentMilestones
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.crud.crud_base import AAPAClass, CRUDbase
from data.crud.crud_factory import registerCRUD
from data.crud.studenten import CRUD_studenten
from database.database import Database
from database.table_def import TableDefinition
from general.timeutil import TSC

class CRUD_milestones(CRUDbase):
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    # superclass_CRUDs: list[CRUDbase] = [], 
                    subclass_CRUDs:dict[str, AAPAClass]={}, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, 
                        #  superclass_CRUDs=superclass_CRUDs, 
                         subclass_CRUDs=subclass_CRUDs,
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def _after_init(self):
        self._db_map['stud_id']['attrib'] = 'student.id'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        # self._db_map['status']['db2obj'] = Milestone.Status
        self._db_map['beoordeling']['db2obj'] = Milestone.Beoordeling
        self._db_map['datum']['db2obj'] = TSC.str_to_timestamp
        self._db_map['datum']['obj2db'] = TSC.timestamp_to_str
    # def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->Student|Bedrijf:
    #     if sub_attrib_name == 'id':
    #         match main_part:
    #             case 'student': 
    #                 return CRUD_studenten(self.database).read(value)
    #             case 'bedrijf': 
    #                 return CRUD_bedrijven(self.database).read(value)
    #     return None

#registerCRUD(CRUD_milestones, class_type=Milestone, table=MilestoneTableDefinition(), subclasses={'student': Student, 'bedrijf': Bedrijf}, autoID=True)

class CRUD_student_milestones(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentMilestonesTableDefinition(), class_type=StudentMilestones, autoID=True)
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
