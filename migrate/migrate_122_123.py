from enum import Enum, auto
from data.classes.studenten import Student
from database.aapa_database import  MijlpaalDirectoryTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentDirectoriesOverzichtDefinition, StudentDirectoryTableDefinition, StudentMijlpaalDirectoriesOverzichtDefinition, StudentVerslagenOverzichtDefinition
from data.classes.student_directories import StudentDirectory
from migrate.migrate import modify_table
from database.classes.sql_view import SQLcreateView
from general.sql_coll import import_json
from database.classes.database import Database

class JsonData:
    class KEY(Enum):
        SET_DIR_STATUS = auto()          
        MP_DIR_DATUM = auto()
        CORRECT_STUD_DIRS = auto()
        CORRECT_MP_DIRS = auto()
        ADAPT_MP_DIRS = auto()
        CREATE_VERSLAGEN = auto()
        REUNITE_ORPHANS  = auto()
        SYNC_BASEDIRS  = auto()
    
    json_data = {   KEY.SET_DIR_STATUS: {'filename': 'set_sdir_status', 'phase':1, 'message': 'setting (computed) status'},
                    KEY.MP_DIR_DATUM: {'filename': 'mp_dir_datum', 'phase':1, 'message': 'setting missing dates'},          
                    KEY.ADAPT_MP_DIRS: {'filename': 'adapt_mp_dirs', 'phase':2, 'message': '"re-engineering" mijlpaal_directories'},
                    KEY.CREATE_VERSLAGEN: {'filename': 'create_verslagen', 'phase':3, 'message': '"re-engineering" verslagen'},
                    KEY.CORRECT_MP_DIRS: {'filename': 'correct_mp_dirs', 'phase':4, 'message': 'correcting double mijlpaal_directories'},
                    KEY.CORRECT_STUD_DIRS: {'filename': 'correct_stud_dirs', 'phase':4, 'message': 'correcting student directories'},
                    KEY.REUNITE_ORPHANS: {'filename': 'reunite_orphans', 'phase':5, 'message': 'reuniting orphan files'},
                    KEY.SYNC_BASEDIRS: {'filename': 'sync_basedir', 'phase':6, 'message': 'Synchronizing database with base directories'},
                }
    @staticmethod
    def execute(database: Database, phase = 0):
        print(f'--- executing generated JSON data files (phase: {phase}) ---')
        for key,entry in JsonData.json_data.items():
            if entry['phase'] > phase:
                continue
            print(f'\t{entry["filename"]}: {entry["message"]}')
            import_json(database, JsonData.get_filename(key))
        print('ready --- executing generated JSON data files.')       
    @staticmethod
    def get_filename(key: KEY)->str:
        if not (entry := JsonData.json_data.get(key, None)):
            return None
        return fr'.\migrate\m123\{entry["filename"]}.json'

def _correct_email_and_delete_double(database: Database, id_keep:int, id_delete: int):
    #dubbelingen, but keep email (correct for second email). the second entry is never used
    #de meeste waren gedaan in 1.22, maar er is er blijkbaar nog 1!
    database._execute_sql_command(f'update STUDENTEN set email=(select email from STUDENTEN as S2 where S2.id=?) where STUDENTEN.id = ?', 
                                  [id_delete,id_keep]
                                  )
    database._execute_sql_command(f'delete from STUDENTEN where id = ?', [id_delete])

def correct_student_errors(database: Database):
    print('correcting some existing errors in STUDENTEN table')  
    #Daan van Boven
    _correct_email_and_delete_double(database, 54, 162)
    print('ready correcting some existing errors in STUDENTEN table')  

def correct_student_status(database: Database):
    print('correcting some modified status STUDENTEN table')  
    #jorn postma
    database._execute_sql_command(f'update STUDENTEN set status=? where id = ?', 
                                  [Student.Status.AFGESTUDEERD, 18])
    print('ready correcting some modified status STUDENTEN table')  

def _copy_student_directories_data(database: Database, old_table_name: str, new_table_name: str)->bool:
    print('copying data') 
    database._execute_sql_command(f'INSERT INTO {new_table_name}(id,stud_id,directory,basedir_id,status) SELECT id,stud_id,directory,basedir_id,{int(StudentDirectory.Status.UNKNOWN)} FROM {old_table_name}')
    return True

def modify_student_directories(database: Database):
    print(f'adding "status" to STUDENT_DIRECTORIES')
    #dropping referencing views first
    database._execute_sql_command(f'DROP VIEW {StudentDirectoriesFileOverzichtDefinition().name}')
    database._execute_sql_command(f'DROP VIEW {StudentDirectoriesOverzichtDefinition().name}')
    modify_table(database, StudentDirectoryTableDefinition(), _copy_student_directories_data)    
    # now re-create views STUDENT_DIRECTORIES_FILE_OVERZICHT en STUDENT_DIRECTORIES_OVERZICHT, 
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))    
    database.execute_sql_command(SQLcreateView(StudentDirectoriesOverzichtDefinition()))    
    print('ready')    

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
    return True

def modify_mijlpaal_directories(database: Database):
    print(f'adding "kans" to MIJLPAAL_DIRECTORIES')
    database._execute_sql_command(f'DROP VIEW {StudentDirectoriesFileOverzichtDefinition().name}')
    modify_table(database, MijlpaalDirectoryTableDefinition(), _copy_mijlpaal_data)
    # must also re-create view StudentDirectoriesFileOverzichtDefinition, because it now references OLD_TABLE_NAME
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))    
    print('ready')

def _correct_path(database: Database, table: str, path_column: str, path_to_correct_pattern: str, replace: str, replace_with: str):
    rows = database._execute_sql_command(f'select id,{path_column} from {table} where {path_column} like ?', [path_to_correct_pattern],True)    
    for row in rows:
        new_path = str(row[path_column]).replace(replace, replace_with)
        database._execute_sql_command(f'update {table} set {path_column}=? where id=?', [new_path, row['id']])

def _correct_path2(database: Database, table_name: str, column_name, error: str, correct: str):
    #lijkt erg op vorige, zo zie je maar. Kan waarschijnlijk beter, maar beide werken.
    rows = database._execute_sql_command(f'select id,{column_name} from {table_name} where {column_name} like ?', 
                                         [fr"%{error}%"],True)
    for row in rows:
        database._execute_sql_command(f'update {table_name} set {column_name}=? where id=?', 
                                  [str(row[f'{column_name}']).replace(error, correct), row['id']])

def _correct_path3(database: Database, table_name: str, column_name, error: str, correct: str):
    #lijkt ook erg op vorige, maar specifiek voor 1 geval.
    rows = database._execute_sql_command(f'select id,{column_name} from {table_name} where {column_name} like ? and timestamp >?', 
                                         [fr"%{error}%","2024"],True)
    for row in rows:
        database._execute_sql_command(f'update {table_name} set {column_name}=? where id=?', 
                                  [str(row[f'{column_name}']).replace(error, correct), row['id']])

def correct_files_for_error(database: Database):
    print('correcting FILES errors, al gecorrigeerd IRL')
    #Micky Cheng
    _correct_path(database, 'FILES', 'filename', r':ROOT12:\Cheng, Micky\2023-12-23%',  "2023-12-23", "2023-12-22")
    _correct_path(database, 'MIJLPAAL_DIRECTORIES', 'directory', r':ROOT12:\Cheng, Micky\2023-12-23%',  "2023-12-23", "2023-12-22")
    #Jarno vd Poll
    _correct_path2(database, 'FILES', 'filename', 'Poll, Jarno', 'Poll, van de, Jarno')
    _correct_path2(database, 'MIJLPAAL_DIRECTORIES', 'directory',  'Poll, Jarno', 'Poll, van de, Jarno')
    #Merlijn Stokhorst
    _correct_path3(database, 'FILES', 'filename', ':ROOT10:', ':ROOT9:')
    #Cassandra van Oosten (Jimi)
    _correct_path(database, 'FILES', 'filename', r':ROOT14:\Oosten, van, Jimi%',  "Jimi", "Cassandra")
    #Fabian de Wilde 
    _correct_path(database, 'FILES', 'filename', r':ROOT7:\Wilde, Fabian%',  "Wilde, Fabian", "Wilde, de, Fabian")
    #Johan van der Meer
    _correct_path(database, 'FILES', 'filename', r':ROOT7:\Meer, Johan van der%',  "Meer, Johan van der", "Meer, van der, Johan")
    #Erik Langendijk
    _correct_path(database, 'FILES', 'filename', r':ROOT7:\Langendijk, Erik (dt)%',  "Langendijk, Erik (dt)", "Langendijk, Erik")
    #Samuel Jansen  
    _correct_path(database, 'FILES', 'filename', r':ROOT9:\Jansen, samuel%',  "Jansen, samuel", "Jansen, Samuel")
    #Luke Glas  
    _correct_path(database, 'FILES', 'filename', r':ROOT7:\Glas, Luke%',  ":ROOT7:", ":ROOT9:")
   

    print('... ready correcting FILES errors')

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        correct_student_errors(database)
        correct_student_status(database)
        modify_mijlpaal_directories(database)
        modify_student_directories(database)
        add_views(database)
        correct_files_for_error(database)
        JsonData.execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        