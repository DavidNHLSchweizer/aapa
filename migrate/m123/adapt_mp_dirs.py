""" ADAPT_MP_DIRS

    Past de mijlpaal_directories aan door de kans toe te voegen (gedetecteerd uit wat er al is)
    De code is bedoeld voor de migratie naar database versie 1.23

"""
from data.general.const import MijlpaalType
from data.classes.studenten import Student
from storage.aapa_storage import AAPAStorage
from storage.queries.student_directories import StudentDirectoryQueries
from main.log import log_warning
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class MijlpalenKansProcessor(MigrationPlugin):
    def init_SQLcollectors(self)->SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set kans=? where id=?'},}))                  
        return sql
    def process_student(self, student: Student):      
        student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        student_directory = student_dir_queries.find_student_dir(student)
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        self.log(f'Student: {student}')
        directories_per_mijlpaal_type = {mijlpaal_type: student_directory.get_directories(mijlpaal_type,sorted=True) 
                                         for mijlpaal_type in MijlpaalType if not mijlpaal_type in {MijlpaalType.AANVRAAG}}        
        for mijlpaal_type in directories_per_mijlpaal_type.keys():
            for n,mp_dir in enumerate(directories_per_mijlpaal_type[mijlpaal_type]):
                mp_dir.kans = n+1
                self.sql.update('mijlpaal_directories', [mp_dir.kans, mp_dir.id])
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:  
        for student in self.storage.queries('studenten').find_all():
            self.process_student(student)
        return True