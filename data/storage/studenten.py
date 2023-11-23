from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.table_registry import register_table
from data.storage.storage_base import StorageBase
from database.database import Database

class StudentenStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, Student, autoID=True)        

    def find_student_by_name_or_email(self, student: Student)->Student:
        for column_name in ['full_name', 'email']:
            if result := self.find_value(column_name, getattr(student, column_name)):
                return result
        return None
    def create_unique_student_nr(self, student: Student)->str:
        n = 1
        if not (result := student.stud_nr):
            result = f'{student.initials()}{n}'
        while self.find_value('stud_nr', result) is not None:
            n+=1
        return result

register_table(class_type=Student, table=StudentTableDefinition(), autoID=True)