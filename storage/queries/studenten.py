from data.classes.studenten import Student
from storage.general.CRUDs import CRUD, CRUDQueries
from storage.general.storage_const import StorageException

class StudentQueries(CRUDQueries):
    def __find_student_by_attribute(self, student: Student, attribute: str)->Student:
        if students:=self.find_values(attributes=attribute, values=getattr(student, attribute)):
            if len(students) > 1:
                raise StorageException(f'More than one student with same {attribute} in database:\n{[str(student) for student in students]}')
            return students[0]        
        return None
    def find_student_by_name_or_email_or_studnr(self, student: Student)->Student:
        if student.full_name and (stored := self.__find_student_by_attribute(student, 'full_name')):
            return stored
        if student.email and (stored := self.__find_student_by_attribute(student, 'email')):
            return stored
        if student.stud_nr and (stored := self.__find_student_by_attribute(student, 'stud_nr')):
            return stored
        return None
    def create_unique_student_nr(self, student: Student)->Student:
        n = 42
        if not (result := student.stud_nr):
            result = f'{student.initials()}{n*42}'
        while self.find_values('stud_nr', result) != []:
            n+=1
        return result
