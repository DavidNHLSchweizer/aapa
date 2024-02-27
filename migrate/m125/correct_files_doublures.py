""" CORRECT_FILES_DOUBLURES. 

    aanpassen van database voor dubbelingen in files.
    
    bedoeld voor migratie db naar versie 1.25
    
"""
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.class_codes import ClassCodes
from database.classes.database import Database
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class FilesReEngineeringProcessor(MigrationPlugin):

    def init_SQLcollectors(self) -> SQLcollectors:
        def insert_query(table_name: str, main_id: str)->str:
            return f'insert into {table_name}({main_id},detail_id,class_code) values (?,?,?)'
        def delete_query(table_name: str, main_id: str)->str:
            return f'delete from {table_name} where {main_id}=? and detail_id=? and class_code=?'
        sql = super().init_SQLcollectors()
        sql.add('aanvragen_details', SQLcollector({'insert': {'sql': insert_query('AANVRAGEN_DETAILS', 'aanvraag_id'),},
                                                   'delete': {'sql': delete_query('AANVRAGEN_DETAILS', 'aanvraag_id'), 'concatenate': False},}))                                                   
        sql.add('verslagen_details', SQLcollector({'insert': {'sql': insert_query('VERSLAGEN_DETAILS', 'verslag_id'),},
                                                   'delete': {'sql': delete_query('VERSLAGEN_DETAILS', 'verslag_id'), 'concatenate': False},}))                                                   
        sql.add('mijlpaal_directories_details', 
                                     SQLcollector({'insert': {'sql': insert_query('MIJLPAAL_DIRECTORIES_DETAILS', 'mp_dir_id'),'concatenate': False},
                                                             'delete': {'sql': delete_query('MIJLPAAL_DIRECTORIES_DETAILS', 'mp_dir_id'),'concatenate': False},}))                                                         
        sql.add('undologs_details', SQLcollector({'insert': {'sql': insert_query('UNDOLOGS_DETAILS', 'log_id'),},
                                                             'delete': {'sql': delete_query('UNDOLOGS_DETAILS', 'log_id'),'concatenate': False},}))
        sql.add('files', SQLcollector({'delete': {'sql':'delete from FILES where id in (?)'},}))
        return sql
    def correct_table(self, main_table: str, file_id1: int, file_id2: int):
        table_name = f'{main_table}_DETAILS'
        fl_code = ClassCodes.classtype_to_code(File)
        query = f'select * from {table_name} WHERE detail_id=? and class_code=?'        
        self.log(table_name)
        for row in self.database._execute_sql_command(query, [file_id2, fl_code], True):
            self.log(Database.convert_row(row))
            #sometimes the correct record is already there (blijkbaar dubbel ingevoerd), easiest just delete first
            self.sql.delete(table_name.lower(), [row[0], file_id1, row['class_code']])           
            self.sql.insert(table_name.lower(), [row[0], file_id1, row['class_code']])           
            self.sql.delete(table_name.lower(), [row[0], row['detail_id'], row['class_code']])           
            self.sql.delete('files', [file_id2])
    def process_double_entry(self, file_id1: int, file_id2: int):
        self.correct_table('AANVRAGEN', file_id1, file_id2)        
        self.correct_table('VERSLAGEN', file_id1, file_id2)        
        self.correct_table('MIJLPAAL_DIRECTORIES', file_id1, file_id2)        
        self.correct_table('UNDOLOGS', file_id1, file_id2)        
    def _get_double_entries(self)->dict:
        query = 'select F.ID as file_id1,F2.id as file_id2 from FILES F, FILES F2 where F.Filename = F2.filename and F.ID<F2.ID'
        rows = self.database._execute_sql_command(query,[], True)
        double_entries = []
        new_entry = None
        for row in rows:
            new_entry = {'file_id1': row['file_id1'], 'file_id2': row['file_id2']}
            double_entries.append(new_entry)
        return double_entries
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        double_entries = self._get_double_entries()
        for entry in double_entries:
            self.process_double_entry(entry['file_id1'], entry['file_id2'])
        self.sql.execute_sql(self.database,  context.preview)
        self.database.commit()
        return True
