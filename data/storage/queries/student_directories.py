from data.classes.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.storage.CRUDs import CRUDQueries

class StudentDirectoryQueries(CRUDQueries):
    def find_student_dir(self, student: Student)->StudentDirectory:
        if stored_id := self.find_max_value('id', where_attributes='student', where_values=student.id):
            return self.crud.read(stored_id)
        return None
    def find_student_mijlpaal_dir(self, student: Student, mijlpaal_type: MijlpaalType)->list[MijlpaalDirectory]:
        if student_directory := self.find_student_dir(student):
            return list(filter(lambda mp_dir: mp_dir.mijlpaal_type == mijlpaal_type, student_directory.directories))
        return []
