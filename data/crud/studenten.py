from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.crud.crud_base import CRUDbase
from data.crud.crud_factory import registerCRUD

class CRUD_studenten(CRUDbase):
    pass

registerCRUD(CRUD_studenten, class_type=Student, table=StudentTableDefinition(), autoID=True)