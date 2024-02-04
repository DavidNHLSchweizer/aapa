from data.aapa_database import  MijlpaalDirectoryTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentMijlpaalDirectoriesOverzichtDefinition
from migrate.migrate import modify_table
from database.sql_view import SQLcreateView
from general.sql_coll import import_json
from database.database import Database

# add new view STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT
def add_view(database: Database):
    print(f'adding STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT')
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))
    print('ready')

# modify new view STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT
def _copy_mijlpaal_data(database: Database, old_table_name: str, new_table_name: str)->bool:
    print('copying data') 
    database._execute_sql_command(f'INSERT INTO {new_table_name} SELECT id,mijlpaal_type,0,directory,datum FROM {old_table_name}')
    # must also re-create view StudentDirectoriesFileOverzichtDefinition, because it now references OLD_TABLE_NAME
    database._execute_sql_command(f'DROP VIEW {StudentDirectoriesFileOverzichtDefinition().name}')
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))
    return True

def modify_mijlpaal_directories(database: Database):
    print(f'adding "kans" to MIJLPAAL_DIRECTORIES')
    modify_table(database, MijlpaalDirectoryTableDefinition(), _copy_mijlpaal_data)
    print('ready')

def create_mijlpaal_directories(database: Database):
    print("re-engineering mijlpaal_directories from generated list SQL-commandos")
    import_json(database, r'.\migrate\m123\create_mp_dirs.json')
    print("... ready re-engineering mijlpaal_directories from generated list SQL-commandos")

def create_verslagen(database: Database):
    print("re-engineering verslagen from generated list SQL-commandos")
    import_json(database, r'.\migrate\m123\create_verslagen.json')
    print("... ready re-engineering verslagen from generated list SQL-commandos")

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_mijlpaal_directories(database)
        if phase == 1:
            create_mijlpaal_directories(database)
        if phase >= 2:
            create_verslagen(database)
        add_view(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        