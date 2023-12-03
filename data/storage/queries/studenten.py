from data.classes.studenten import Student
from data.storage.CRUDs import CRUD, CRUDQueries
from data.storage.general.storage_const import StorageException

class StudentenQueries(CRUDQueries):
    def __find_student_by_attribute(self, student: Student, attribute: str)->Student:
        if students:=self.find_values(attributes=attribute, values=getattr(student, attribute)):
            if len(students) > 1:
                raise StorageException(f'More than one student with same {attribute} in database:\n{[str(student) for student in students]}')
            return students[0]        
        return None
    def find_student_by_name_or_email(self, student: Student)->Student:
        if (student := self.__find_student_by_attribute(student, 'full_name')):
            return student
        if (student := self.__find_student_by_attribute(student, 'email')):
            return student
        return None
    def create_unique_student_nr(self, student: Student)->Student:
        n = 42
        if not (result := student.stud_nr):
            result = f'{student.initials()}{n*42}'
        while self.find_values('stud_nr', result) is not []:
            n+=1
        return result
