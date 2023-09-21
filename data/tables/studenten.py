from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import StudentTableDefinition
from data.classes import StudentInfo
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops

class CRUD_studenten(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentTableDefinition())
        self._db_map['stud_nr']['attrib'] = 'studnr'
        self._db_map['full_name']['attrib'] = 'student_name'
        self._db_map['tel_nr']['attrib'] = 'telno'
    # def create(self, studInfo: StudentInfo):
    #     super().create(columns=self._get_all_columns(), values=self._get_all_values(studInfo))   
    def read(self, studnr: str)->StudentInfo:
        if row:=super().read(where=SQE(self.table.keys[0], Ops.EQ, studnr)):
            return StudentInfo(student_name=row['full_name'], studnr=studnr, telno=row['tel_nr'], email=row['email']) 
        else:
            return None
    def update(self, studInfo: StudentInfo):
        super().update(columns=self._get_all_columns(False), values=self._get_all_values(studInfo, False), 
                       where=SQE(self.table.keys[0], Ops.EQ, studInfo.studnr))
    # def delete(self, studnr: str):
    #     super().delete(where=SQE(self.table.keys[0], Ops.EQ, studnr))


