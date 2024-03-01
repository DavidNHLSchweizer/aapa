from pathlib import Path
from data.general.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.general.roots import Roots
from storage.general.CRUDs import CRUDQueries

class StudentDirectoriesQueries(CRUDQueries):
    def find_student_dir(self, student: Student)->StudentDirectory:
        if stored_id := self.find_max_value('id', where_attributes='student', where_values=student.id):
            return self.crud.read(stored_id)
        return None
    def find_student_dirs(self, student: Student)->list[StudentDirectory]:
        return self.find_values(attributes='student', values=student.id, map_values=False)
    def find_student_dir_for_directory(self, student: Student, directory: str)->StudentDirectory:
        if stored := self.find_values(attributes=['student','directory'], values=[student,directory]):
            return stored[0]
        return None
    def find_student_mijlpaal_dir(self, student: Student, mijlpaal_type: MijlpaalType, kans: int = 0)->list[MijlpaalDirectory]:
        if student_directory := self.find_student_dir(student):
            if kans:
                return list(filter(lambda mp_dir: mp_dir.mijlpaal_type == mijlpaal_type and mp_dir.kans==kans, student_directory.directories))
            else:
                return list(filter(lambda mp_dir: mp_dir.mijlpaal_type == mijlpaal_type, student_directory.directories))
        return []
    def find_student_dir_from_directory(self, directory: str|Path)->list[StudentDirectory]:
        return self.find_values(attributes='directory', values=str(directory))
    