from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import StudentTableDefinition
from data.classes.studenten import StudentInfo
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops

class CRUD_studenten(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition(), StudentInfo)
    # def update(self, student: StudentInfo):
    #     super().update(columns=self._get_all_columns(False), values=self._get_all_values(student, False), 
    #                    where=SQE(self.table.keys[0], Ops.EQ, student.stud_nr))


