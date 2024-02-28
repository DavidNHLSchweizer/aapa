""" CORRECT_MISSING_AANVRAGEN_FILES. 

    aanpassen van database voor ontbrekende files in aanvragen (aanvragen met 0 files).
    
    bedoeld voor migratie db naar versie 1.25
    
"""
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.class_codes import ClassCodes
from data.general.const import MijlpaalType
from database.classes.database import Database
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class AanvragenFilesReEngineeringProcessor(MigrationPlugin):

    def init_SQLcollectors(self) -> SQLcollectors:
        def insert_query(table_name: str, main_id: str)->str:
            return f'insert into {table_name}({main_id},detail_id,class_code) values (?,?,?)'
        sql = super().init_SQLcollectors()
        sql.add('aanvragen_details', SQLcollector({'insert': {'sql': insert_query('AANVRAGEN_DETAILS', 'aanvraag_id'),}}
                                                   ))                                                   
        return sql
    def process_problem_aanvraag(self, aanvraag: Aanvraag):
        print(f'Aanvraag: {aanvraag.summary()}; Aanvraag id: {aanvraag.id}\n\tAanvraag dir: {File.display_file(aanvraag.get_directory(File.Type.AANVRAAG_PDF))}')
        # print(f'\tFiles:\n{"\n\t\t".join([f'{file.id}: {File.display_file(file.filename)}' for file in aanvraag.files_list])}')
        stud_dir = self.student_dir_queries.find_student_dir(aanvraag.student)
        mp_dir = stud_dir.get_directory(aanvraag.datum,MijlpaalType.AANVRAAG)
        # print(mp_dir)
        for file in mp_dir.files_list:
            self.sql.insert('aanvragen_details', [aanvraag.id, file.id, self.file_code])
    def _get_problem_aanvragen(self)->dict:
        return self.storage.find_values('aanvragen', 'id', set(range(227,234)))
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        self.file_code = ClassCodes.classtype_to_code(File)
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        problem_aanvragen = self._get_problem_aanvragen()
        for entry in problem_aanvragen:
            self.process_problem_aanvraag(entry)
        self.sql.execute_sql(self.database,  context.preview)
        self.database.commit()
        return True
