""" CORRECT_FILES_IN_WEEK. 

    aanpassen van database voor files die bij aanvragen in de "Week" staan.
    corrigeren vanuit bestaande mp_directory
    
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

class AanvragenFilesReEngineering2Processor(MigrationPlugin):

    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('aanvragen_details', SQLcollector({'insert': {'sql': self.insert_detail_query('AANVRAGEN', 'aanvraag_id')},
                                                   'delete': {'sql': self.delete_detail_query('AANVRAGEN', 'aanvraag_id'),'concatenate': False}}
                                                   ))                                                   
        return sql
    def _aanvraag_file_in_week_directory(self, aanvraag: Aanvraag, file: File)->bool:
        return file.filetype in {File.Type.AANVRAAG_PDF,File.Type.GRADE_FORM_PDF} and \
            self.week_pattern.match(file.filename) is not None
    def _copy_files(self, aanvraag: Aanvraag):
        if not (mp_dirs := self.stud_dir_queries.find_student_mijlpaal_dir(aanvraag.student,MijlpaalType.AANVRAAG)):
            return 
        mp_dir:MijlpaalDirectory = mp_dirs[-1]
        aanvraag_files_ids= set()
        for file in aanvraag.files_list:
            aanvraag_files_ids.add(file.id)
            # remove files that are also in the mp_dir list
            if self._aanvraag_file_in_week_directory(aanvraag, file):
                filename = Path(file.filename).name
                if filename in [Path(file.filename).name for file in mp_dir.files_list]:
                    self.sql.delete('aanvragen_details', [aanvraag.id, file.id, self.file_code])
        # link everythin in mp_dir to aanvraag
        for file in mp_dir.files_list:
            if not file.id in aanvraag_files_ids:
                self.sql.insert('aanvragen_details', [aanvraag.id, file.id, self.file_code])
    def _process_aanvraag(self, aanvraag: Aanvraag):
        directory = aanvraag.get_directory(File.Type.AANVRAAG_PDF)              
        if not directory or self.week_pattern.match(directory):
            if aanvraag.status in AanvraagStatus.active_states():
                log_error(f'Probleem with {aanvraag.summary()} [{aanvraag.id}].\nStatus ({aanvraag.status}) is actief. Kan dit niet meer oplossen...')
                return
            self._copy_files(aanvraag)
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        self.file_code = ClassCodes.classtype_to_code(File)
        self.stud_dir_queries:StudentDirectoriesQueries=self.storage.queries('student_directories')
        self.mp_dir_queries: MijlpaalDirectoriesQueries = self.storage.queries('mijlpaal_directories')
        self.week_pattern = re.compile(r'.*week [\d]+.*',re.IGNORECASE)
        return True

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        for aanvraag in sorted(self.storage.queries('aanvragen').find_all(),key=lambda a:a.student.id):
            self._process_aanvraag(aanvraag)                               
        self.sql.execute_sql(self.database,  context.preview)
        self.database.commit()
        return True