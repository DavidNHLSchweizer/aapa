""" ADAPT_MP_DIRS

    Past de mijlpaal_directories aan door de kans toe te voegen (gedetecteerd uit wat er al is)
    De code is bedoeld voor de migratie naar database versie 1.23

"""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from data.classes.const import MijlpaalType
from data.classes.studenten import Student
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.student_directories import StudentDirectoryQueries
from extra.tools import get_json_filename
from general.log import init_logging, log_info, log_print, log_warning
from general.preview import Preview
from general.timeutil import TSC
from general.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext

class MijlpalenKansProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.sql = SQLcollectors()
        self.sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set kans=? where id=?'},}))                  
    def process_student(self, student: Student, preview=False):      
        student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        student_directory = student_dir_queries.find_student_dir(student)
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        log_info(f'Student: {student}',to_console=True)
        directories_per_mijlpaal_type = {mijlpaal_type: student_directory.get_directories(mijlpaal_type,sorted=True) 
                                         for mijlpaal_type in MijlpaalType if not mijlpaal_type in {MijlpaalType.AANVRAAG}}        
        for mijlpaal_type in directories_per_mijlpaal_type.keys():
            for n,mp_dir in enumerate(directories_per_mijlpaal_type[mijlpaal_type]):
                mp_dir.kans = n+1
                self.sql.update('mijlpaal_directories', [mp_dir.kans, mp_dir.id])
    def process_all(self,  migrate_dir = None):        
        for student in self.storage.queries('studenten').find_all():
            self.process_student(student, preview=True)
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
    storage = context.configuration.storage
    with Preview(True,storage,'Update mijlpaal_directories (voor migratie)'):
        processor = MijlpalenKansProcessor(storage)
        processor.process_all(migrate_dir=migrate_dir)
