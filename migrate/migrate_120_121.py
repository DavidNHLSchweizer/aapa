import datetime
import re
from typing import Tuple
from database.aapa_database import BaseDirsTableDefinition, MijlpaalDirectory_FilesTableDefinition, MijlpaalDirectoriesTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentDirectoriesOverzichtDefinition, StudentDirectory_DirectoriesTableDefinition, \
        StudentDirectoriesTableDefinition, UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, VerslagFilesTableDefinition, VerslagenTableDefinition, \
        create_roots
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from migrate.m119.old_roots import old_add_root, old_decode_path, old_reset_roots
from general.sql_coll import SQLcollectors
from data.general.roots import OneDriveCoder, add_root, encode_path, get_onedrive_root, reset_roots
from storage.aapa_storage import AAPAStorage
from database.classes.database import Database
from database.classes.sql_table import SQLcreateTable
from database.classes.sql_view import SQLcreateView
from database.classes.table_def import TableDefinition
import database.classes.dbConst as dbc
from general.keys import reset_key
from general.timeutil import TSC

# correct error in undo_logs_aanvragen

def _correct_table(database: Database, table_definition: TableDefinition):
    table_name = table_definition.name
    old_table_name = f'OLD_{table_name}'
    print(f'correcting {table_name}')
    database._execute_sql_command(f'alter table {table_name} rename to {old_table_name}')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(table_definition))
    print( 'copying data')
    database._execute_sql_command(f'INSERT INTO {table_name} SELECT * FROM {old_table_name}')
    database._execute_sql_command(f'drop table {old_table_name}')
    print('ready')

def correct_error_undo_logs_aanvragen(database: Database):
    print('Corrigeren fouten in foreign key definitie voor UNDOLOGS_AANVRAGEN en UNDOLOGS_FILES' )
    _correct_table(database, UndoLogAanvragenTableDefinition())
    _correct_table(database, UndoLogFilesTableDefinition())
    print('--- klaar corrigeren fout in foreign key definitie voor UNDOLOGS_AANVRAGEN')
    
def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        correct_error_undo_logs_aanvragen(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.

        # 
        