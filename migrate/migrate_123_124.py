from dataclasses import dataclass
from enum import Enum, auto
from database.aapa_database import UndoLogTableDefinition, UndoLogVerslagenTableDefinition
from database.classes.sql_table import SQLcreateTable
from main.options import AAPAProcessingOptions
from migrate.migrate import JsonData, modify_table
from database.classes.database import Database
 
class M124JsonData(JsonData):
    class KEY(Enum):
        CREATE_VERSLAGEN = auto()  
    def __init__(self):
        super().__init__(r'migrate\m124')
        self.init_entries()
    def init_entries(self):
        self.add_entry(self.KEY.CREATE_VERSLAGEN,filename='create_verslagen', phase=1, message ='"re-engineering" verslagen update')

def delete_verslagen(database: Database):
    #remove verslagen die per ongeluk incorrect in de database te recht zijn gekomen
    print('removing verslagen records that need to be recreated')
    database._execute_sql_command(f'DELETE from VERSLAGEN_FILES where verslag_id >= 564')
    database._execute_sql_command(f'DELETE from VERSLAGEN where id >= 564')
    print('klaar removing verslagen records that need to be recreated')

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
        delete_verslagen(database)
        M124JsonData().execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
         # 
        