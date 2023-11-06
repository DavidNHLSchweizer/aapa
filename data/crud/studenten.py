from data.AAPdatabase import StudentTableDefinition
from data.classes.studenten import Student
from data.crud.crud_base import CRUDbaseAuto
from database.database import Database

class CRUD_studenten(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition(), Student)


