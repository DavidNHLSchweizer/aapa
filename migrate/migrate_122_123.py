from data.aapa_database import  StudentMijlpaalDirectoriesOverzichtDefinition
from data.classes.studenten import Student
from database.sql_view import SQLcreateView
from general.sql_coll import import_json
from database.database import Database
from database.sql_table import SQLcreateTable

# add new view STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT
def add_view(database: Database):
    print(f'adding STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT')
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))
    print('ready')
   
def create_verslagen(database: Database):
    print("re-engineering verslagen from generated list SQL-commandos")
    import_json(database, r'.\migrate\m123\create_verslagen.json')
    print("... ready re-engineering verslagen from generated list SQL-commandos")

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        add_view(database)
        create_verslagen(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        