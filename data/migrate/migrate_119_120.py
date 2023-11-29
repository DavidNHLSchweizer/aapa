from data.aapa_database import BaseDirsTableDefinition, StudentAanvragenTableDefinition, StudentMilestonesTableDefinition, StudentVerslagenTableDefinition, VerslagFilesTableDefinition, VerslagTableDefinition
from data.migrate.migrate_118_119 import _init_base_directories
from database.database import Database
from database.sql_table import SQLcreateTable

# toevoegen VERSLAGEN tabel en BASEDIRS tabel
# toevoegen STUDENT_MILESTONES en STUDENT_MILESTONES_DETAILS tabel

def create_verslagen_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN en VERSLAG_FILES')
    database.execute_sql_command(SQLcreateTable(VerslagTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagFilesTableDefinition()))
    print('toevoegen nieuwe tabel BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    print('initialiseren waardes voor BASEDIRS')
    _init_base_directories(database)
    print('toevoegen nieuwe STUDENT_MILESTONES, STUDENT_AANVRAGEN en STUDENT_VERSLAGEN tabellen')
    database.execute_sql_command(SQLcreateTable(StudentMilestonesTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(StudentAanvragenTableDefinition())) 
    database.execute_sql_command(SQLcreateTable(StudentVerslagenTableDefinition())) 
    print('--- klaar toevoegen nieuwe tabellen')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        create_verslagen_tables(database)
