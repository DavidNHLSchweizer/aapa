""" SET_SDIR_STATUS. 

    aanpassen van database voor initialisatie status in student_directories.
    bedoeld voor migratie naar versie 1.23
    
"""
from data.classes.files import File
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from storage.queries.student_directories import StudentDirectoryQueries
from main.log import log_warning
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class StudentDirectoriesStatusProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('student_directories', SQLcollector({'update': {'sql':'update STUDENT_DIRECTORIES set status=? where id=?'},}))
        return sql
    def _sql_set_status(self, student_directory: StudentDirectory, status: StudentDirectory.Status):
        student_directory.status = status
        self.sql.update('student_directories', [int(status), student_directory.id])
    def process_student(self, student: Student):      
        self.log(f'{student}:')
        student_directories:list[StudentDirectory] = sorted(self.student_dir_queries.find_values(attributes='student', values=student),
                                     key=lambda sd: sd.id)
        if not student_directories:
            log_warning(f'Geen enkele directory gevonden voor student {student}.')
            return
        if student.status in {Student.Status.AFGESTUDEERD, Student.Status.GESTOPT}:
            for stud_dir in student_directories:
                self._sql_set_status(stud_dir,StudentDirectory.Status.ARCHIVED)
        else:
            for stud_dir in student_directories[:-1]:
                self._sql_set_status(stud_dir,StudentDirectory.Status.ARCHIVED)
            self._sql_set_status(student_directories[-1],StudentDirectory.Status.ACTIVE)
        for stud_dir in student_directories:
            self.log(f'{File.display_file(stud_dir.directory)}: {stud_dir.status}')

        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        for student in sorted(self.storage.queries('studenten').find_all(),key=lambda s: s.full_name):
            self.process_student(student)
        return True
