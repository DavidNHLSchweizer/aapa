from database.aapa_database import UndoLogTableDefinition, UndoLogVerslagenTableDefinition
from database.classes.sql_table import SQLcreateTable
from main.options import AAPAProcessingOptions
from migrate.migrate import modify_table
from database.classes.sql_view import SQLcreateView
from general.sql_coll import import_json
from database.classes.database import Database

# class JsonData:
#     class KEY(Enum):
#         SET_DIR_STATUS = auto()          
#         MP_DIR_DATUM = auto()
#         CORRECT_STUD_DIRS = auto()
#         CORRECT_MP_DIRS = auto()
#         ADAPT_MP_DIRS = auto()
#         CREATE_VERSLAGEN = auto()
#         REUNITE_ORPHANS  = auto()
#         SYNC_BASEDIRS  = auto()
    
#     json_data = {   KEY.SET_DIR_STATUS: {'filename': 'set_sdir_status', 'phase':1, 'message': 'setting (computed) status'},
#                     KEY.MP_DIR_DATUM: {'filename': 'mp_dir_datum', 'phase':1, 'message': 'setting missing dates'},          
#                     KEY.ADAPT_MP_DIRS: {'filename': 'adapt_mp_dirs', 'phase':2, 'message': '"re-engineering" mijlpaal_directories'},
#                     KEY.CREATE_VERSLAGEN: {'filename': 'create_verslagen', 'phase':3, 'message': '"re-engineering" verslagen'},
#                     KEY.CORRECT_MP_DIRS: {'filename': 'correct_mp_dirs', 'phase':4, 'message': 'correcting double mijlpaal_directories'},
#                     KEY.CORRECT_STUD_DIRS: {'filename': 'correct_stud_dirs', 'phase':4, 'message': 'correcting student directories'},
#                     KEY.REUNITE_ORPHANS: {'filename': 'reunite_orphans', 'phase':5, 'message': 'reuniting orphan files'},
#                     KEY.SYNC_BASEDIRS: {'filename': 'sync_basedir', 'phase':6, 'message': 'Synchronizing database with base directories'},
#                 }
#     @staticmethod
#     def execute(database: Database, phase = 0):
#         print(f'--- executing generated JSON data files (phase: {phase}) ---')
#         for key,entry in JsonData.json_data.items():
#             if entry['phase'] > phase:
#                 continue
#             print(f'\t{entry["filename"]}: {entry["message"]}')
#             import_json(database, JsonData.get_filename(key))
#         print('ready --- executing generated JSON data files.')       
#     @staticmethod
#     def get_filename(key: KEY)->str:
#         if not (entry := JsonData.json_data.get(key, None)):
#             return None
#         return fr'.\migrate\m123\{entry["filename"]}.json'


def _copy_undolog_data(database: Database, old_table_name: str, new_table_name: str)->bool:
    print('copying data') 
    select = f'SELECT id,description,action,{int(AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN)},user,date,can_undo FROM {old_table_name}'
    database._execute_sql_command(f'INSERT INTO {new_table_name}(id,description,action,processing_mode,user,date,can_undo) {select}')
    return True

def modify_undo_logs(database: Database):
    print(f'adding "processing_mode" to UNDOLOGS')
    modify_table(database, UndoLogTableDefinition(), _copy_undolog_data)    
    # add new UNDOLOG_VERSLAGEN table    
    database.execute_sql_command(SQLcreateTable(UndoLogVerslagenTableDefinition()))  
    print('ready')    

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_undo_logs(database)
        # JsonData.execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        