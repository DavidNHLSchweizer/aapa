from data.aapa_database import  MijlpaalDirectoryTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentMijlpaalDirectoriesOverzichtDefinition, StudentVerslagenOverzichtDefinition
from migrate.migrate import modify_table
from database.sql_view import SQLcreateView
from general.sql_coll import import_json
from database.database import Database

# add new views
def add_views(database: Database):
    print(f'adding new views STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT en STUDENT_VERSLAGEN_OVERZICHT')
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentVerslagenOverzichtDefinition()))
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

def _correct_path(database: Database, table: str, path_column: str, path_to_correct_pattern: str, replace: str, replace_with: str):
    rows = database._execute_sql_command(f'select id,{path_column} from {table} where {path_column} like ?', [path_to_correct_pattern],True)    
    for row in rows:
        new_path = str(row[path_column]).replace(replace, replace_with)
        database._execute_sql_command(f'update {table} set {path_column}=? where id=?', [new_path, row['id']])

def correct_files_for_error(database: Database):
    print('correcting FILES errors, al gecorrigeerd IRL')
    _correct_path(database, 'FILES', 'filename', r':ROOT12:\Cheng, Micky\2023-12-23%',  "2023-12-23", "2023-12-22")
    _correct_path(database, 'MIJLPAAL_DIRECTORIES', 'directory', r':ROOT12:\Cheng, Micky\2023-12-23%',  "2023-12-23", "2023-12-22")
    print('... ready correcting FILES errors')
    

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_mijlpaal_directories(database)
        if phase == 1:
            create_mijlpaal_directories(database)
        if phase >= 2:
            create_verslagen(database)
        add_views(database)
        correct_files_for_error(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        