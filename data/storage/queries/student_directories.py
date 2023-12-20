from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.storage.CRUDs import CRUDQueries

class StudentDirectoryQueries(CRUDQueries):
    def find_student_dir(self, student: Student)->StudentDirectory:
        if stored_id := self.find_max_value('id', where_attributes='student', where_values=student.id):
            return self.crud.read(stored_id)
        return None
