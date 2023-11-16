# from data.classes.bedrijven import Bedrijf
# from data.classes.milestones import Milestone
# from data.classes.studenten import Student
# from data.crud.studenten import CRUD_studenten
# from data.AAPdatabase import MilestoneTableDefinition
# from data.crud.crud_base import CRUDbaseAuto
# from database.database import Database

# class CRUD_milestones(CRUDbaseAuto):
#     def __init__(self, database: Database):
#         super().__init__(database, MilestoneTableDefinition(), Milestone)
#         self._db_map['stud_nr']['attrib'] = 'student.stud_nr'
#     def _read_sub_attrib(self, sub_attrib_name: str, value)->type[Student|Bedrijf]:
#         match sub_attrib_name:
#             case _: return None

