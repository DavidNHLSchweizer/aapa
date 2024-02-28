""" ADD_VERSLAGEN_TO_MP_DIRS. 

    aanpassen van database: voeg verslagen toe aan mijlpalendirectories voor alle bekende verslagen.
    
    bedoeld voor migratie db naar versie 1.25
    
"""
from pathlib import Path
import re
from data.classes.verslagen import Verslag
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.class_codes import ClassCodes
from data.general.const import AanvraagStatus, MijlpaalType
from database.classes.database import Database
from main.log import log_error
from storage.queries.mijlpaal_directories import MijlpaalDirectoriesQueries
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class AanvragenToevoegenProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('mijlpaal_directories_details', SQLcollector({'insert': {'sql': self.insert_detail_query('MIJLPAAL_DIRECTORIES', 'mp_dir_id')},}
                                                   ))                                                   
        return sql
    def _find_mp_dir_from_verslag(self, verslag: Verslag)->MijlpaalDirectory:
        if not (mp_dirs := self.stud_dir_queries.find_student_mijlpaal_dir(verslag.student,verslag.mijlpaal_type, verslag.kans)):
            return None
        return mp_dirs[-1]        
    def find_mp_dir_verslag(self, verslag: Verslag)->MijlpaalDirectory:
        directory = verslag.get_directory(verslag.mijlpaal_type.default_filetype())              
        if directory:
            return self.mp_dir_queries.find_mijlpaal_directory(directory)
        return self._find_mp_dir_from_verslag(verslag)
    def _process_verslag(self, verslag: Verslag):
        print(verslag.summary())
        try:
            mp_dir = self.find_mp_dir_verslag(verslag)
            if not mp_dir:
                print('====================')
                log_error(f'Mijlpaal Directory not found for verslag {verslag}')
                print(f'Mijlpaal Directory not found for verslag {verslag} [{verslag.id}]' )
                print('====================')
            else:
                mp_dir.mijlpalen.add(verslag)
                self.sql.insert('mijlpaal_directories_details', [mp_dir.id, verslag.id, self.verslag_code])
        except Exception as E:
            print('====================')
            print(f'Exception: {E}')
            print('====================')
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        self.verslag_code = ClassCodes.classtype_to_code(Verslag)
        self.stud_dir_queries:StudentDirectoriesQueries=self.storage.queries('student_directories')
        self.mp_dir_queries: MijlpaalDirectoriesQueries = self.storage.queries('mijlpaal_directories')
        self.week_pattern = re.compile(r'.*week [\d]+.*',re.IGNORECASE)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        for verslag in sorted(self.storage.queries('verslagen').find_all(),key=lambda a:a.student.id):
        # if verslag := self.storage.read('verslagen', 219):
            self._process_verslag(verslag)                               
        self.sql.execute_sql(self.database,  context.preview)
        return True