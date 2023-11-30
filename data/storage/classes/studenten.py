from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.CRUDs import CRUD, register_crud

class StudentenStorage(CRUD):
    def find_student_by_name_or_email(self, student: Student)->Student:
        for column_name in ['full_name', 'email']:
            if result := self.find_value(column_name, getattr(student, column_name)):
                return result[0]
        return None
    def create_unique_student_nr(self, student: Student)->str:
        n = 1
        if not (result := student.stud_nr):
            result = f'{student.initials()}{n}'
        while self.find_value('stud_nr', result) is not None:
            n+=1
        return result
    def find_value(self, column_name: str, attribute: str):
        raise NotImplemented('find value')

register_crud(class_type=Student, 
                table=StudentTableDefinition(), 
                crud=StudentenStorage)