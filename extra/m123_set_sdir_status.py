""" M123_SET_SDIR_STATUS. 

    aanpassen van database voor initialisatie status in student_directories.
    bedoeld voor migratie naar versie 1.23
    
"""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.student_directories import StudentDirectoryQueries
from extra.tools import get_json_filename
from general.fileutil import last_parts_file
from general.log import log_print, log_warning
from general.preview import Preview
from general.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext

class StudentDirectoriesStatusProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.sql = SQLcollectors()
        self.sql.add('student_directories', SQLcollector({'update': {'sql':'update STUDENT_DIRECTORIES set status=? where id=?'},}))
    def _sql_set_status(self, student_directory: StudentDirectory, status: StudentDirectory.Status):
        student_directory.status = status
        self.sql.update('student_directories', [int(status), student_directory.id])
    def process_student(self, student: Student):      
        log_print(f'{student}:')
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
            log_print(f'{last_parts_file(stud_dir.directory)}: {stud_dir.status}')

    def process_all(self,  migrate_dir = None):        
        log_print('----------------------------------')
        for student in sorted(self.storage.queries('studenten').find_all(),key=lambda s: s.full_name):
            self.process_student(student)
        if migrate_dir:            
            filename = Path(migrate_dir).resolve().joinpath(get_json_filename(__file__))
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')

def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    context.processing_options.debug = True
    context.processing_options.preview = True

    migrate_dir=namespace.migrate if 'migrate' in namespace else None
    print(migrate_dir)
    storage = context.configuration.storage
    with Preview(True,storage,'Initialiseer status voor student_directories'):
        StudentDirectoriesStatusProcessor(storage).process_all(migrate_dir)

