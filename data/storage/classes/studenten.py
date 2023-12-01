from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.CRUDs import CRUDhelper, register_crud

class StudentenCRUDhelper(CRUDhelper): pass


register_crud(class_type=Student, 
                table=StudentTableDefinition(),
                helper_type=StudentenCRUDhelper
                )