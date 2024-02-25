import datetime
import re
from typing import Tuple
from database.aapa_database import BaseDirsTableDefinition, MijlpaalDirectory_FilesTableDefinition, MijlpaalDirectoriesTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentDirectoriesOverzichtDefinition, StudentDirectory_DirectoriesTableDefinition, \
        StudentDirectoriesTableDefinition, UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, VerslagFilesTableDefinition, VerslagenTableDefinition, \
        create_roots
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from migrate.m119.old_roots import old_add_root, old_decode_path, old_reset_roots
from general.sql_coll import SQLcollectors, import_json
from data.general.roots import OneDriveCoder, add_root, encode_path, get_onedrive_root, reset_roots
from storage.aapa_storage import AAPAStorage
from database.classes.database import Database
from database.classes.sql_table import SQLcreateTable
from database.classes.sql_view import SQLcreateView
from database.classes.table_def import TableDefinition
import database.classes.dbConst as dbc
from general.keys import reset_key
from general.timeutil import TSC

# remove directory column from VERSLAGEN table
def modify_VERSLAGEN(database: Database):
    print(f'correcting VERSLAGEN')
    table = VerslagenTableDefinition()
    old_table_name = f'OLD_{table.name}'
    database._execute_sql_command(f'alter table {table.name} rename to {old_table_name}')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(table))
    # print( 'copying data') THIS part IS NOT NEEDED (and produces an error message) because the old table is empty anyway
    # database._execute_sql_command(f'INSERT INTO {table.name}(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer) SELECT (id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer) FROM {old_table_name}')
    database._execute_sql_command(f'drop table {old_table_name}')
    print('ready')
   
def _correct_email_and_delete_double(database: Database, id_keep:int, id_delete: int):
    #dubbelingen, but keep email (correct for second email). the second entry is never used
    database._execute_sql_command(f'update STUDENTEN set email=(select email from STUDENTEN as S2 where S2.id=?) where STUDENTEN.id = ?', 
                                  [id_delete,id_keep]
                                  )
    database._execute_sql_command(f'delete from STUDENTEN where id = ?', [id_delete])

def correct_student_errors(database: Database):
    print('correcting some existing errors in STUDENTEN table')  

    #status Daan Eekhof,Michael Koopmans (inmiddels afgestudeerd)
    database._execute_sql_command(f'update STUDENTEN set STATUS=? where id in (?,?)', 
                                [Student.Status.AFGESTUDEERD, 102,122])
    #correctie enkele dubbelingen
    #Hidde de Vries
    _correct_email_and_delete_double(database, 59, 96)
    #Fabian de Wilde
    _correct_email_and_delete_double(database, 67, 97)
    #Tycho vd Duim
    _correct_email_and_delete_double(database, 55, 163)

    #execute correcties in create_aanvragen.json
    print("importing aanvragen from generated list SQL-commandos")
    import_json(database, r'.\migrate\m122\create_aanvragen.json')
    print("... ready importing student directories from generated list SQL-commandos")
    
def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_VERSLAGEN(database)
        if phase > 1:
            correct_student_errors(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        