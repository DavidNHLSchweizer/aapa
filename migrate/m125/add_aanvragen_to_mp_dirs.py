""" ADD_AANVRAGEN_TO_MP_DIRS. 

    aanpassen van database: voeg aanvragen toe aan mijlpalendirectories voor alle bekende aanvragen.
    
    bedoeld voor migratie db naar versie 1.25
    
"""
from pathlib import Path
import re
from data.classes.aanvragen import Aanvraag
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
    def _find_mp_dir_from_aanvraag(self, aanvraag: Aanvraag)->MijlpaalDirectory:
        if not (mp_dirs := self.stud_dir_queries.find_student_mijlpaal_dir(aanvraag.student,MijlpaalType.AANVRAAG)):
            return None
        return mp_dirs[-1]        
    def find_mp_dir_aanvraag(self, aanvraag: Aanvraag)->MijlpaalDirectory:
        directory = aanvraag.get_directory(File.Type.AANVRAAG_PDF)              
        if directory and not self.week_pattern.match(directory):
            return self.mp_dir_queries.find_mijlpaal_directory(directory)
        return self._find_mp_dir_from_aanvraag(aanvraag)
    def _process_aanvraag(self, aanvraag: Aanvraag):
        try:
            mp_dir = self.find_mp_dir_aanvraag(aanvraag)
            if not mp_dir:
                print('====================')
                log_error(f'Mijlpaal Directory not found for aanvraag {aanvraag}')
                print(f'Mijlpaal Directory not found for aanvraag {aanvraag} [{aanvraag.id}]' )
                print('====================')
            else:
                mp_dir.mijlpalen.add(aanvraag)
                self.sql.insert('mijlpaal_directories_details', [mp_dir.id, aanvraag.id, self.aanvraag_code])
        except Exception as E:
            print('====================')
            print(f'Exception: {E}')
            print('====================')
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        self.aanvraag_code = ClassCodes.classtype_to_code(Aanvraag)
        self.stud_dir_queries:StudentDirectoriesQueries=self.storage.queries('student_directories')
        self.mp_dir_queries: MijlpaalDirectoriesQueries = self.storage.queries('mijlpaal_directories')
        self.week_pattern = re.compile(r'.*week [\d]+.*',re.IGNORECASE)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        for aanvraag in sorted(self.storage.queries('aanvragen').find_all(),key=lambda a:a.student.id):
            self._process_aanvraag(aanvraag)                               
        self.sql.execute_sql(self.database,  context.preview)
        return True