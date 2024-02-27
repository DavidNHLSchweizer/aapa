""" migratie naar database v1.24

Aanpassingen voor verslagen.

"""
from enum import Enum, IntEnum, auto
from data.general.const import VerslagStatus
from database.aapa_database import UndoLogsTableDefinition,  VerslagenTableDefinition
from database.classes.sql_table import SQLcreateTable
from database.classes.sql_view import SQLcreateView
from main.options import AAPAProcessingOptions
from migrate.m124.obsolete import  UndoLogVerslagenTableDefinition, oldStudentVerslagenOverzichtDefinition
from migrate.migrate import JsonData, modify_table
from database.classes.database import Database
 
class M124JsonData(JsonData):
    class KEY(Enum):
        CREATE_VERSLAGEN = auto()  
        CORRECT_MP_DIRS = auto()
        ADD_ORPHAN_VERSLAGEN = auto()
    def __init__(self):
        super().__init__(r'migrate\m124')
        self.init_entries()
    def init_entries(self):
        self.add_entry(self.KEY.CORRECT_MP_DIRS,filename='correct_mp_dirs', phase=1, message ='correcting inconsistencies in mijlpaal_directories')
        self.add_entry(self.KEY.CREATE_VERSLAGEN,filename='create_verslagen', phase=2, message ='"re-engineering" verslagen update')
        self.add_entry(self.KEY.ADD_ORPHAN_VERSLAGEN,filename='add_orphan_verslagen', phase=3, message ='correcting verslagen without any files attached')

class OldVerslagStatus(IntEnum):
    LEGACY          = -2
    INVALID         = -1
    NEW             = 0
    NEEDS_GRADING   = 1
    NEW_MULTIPLE    = 2
    GRADED          = 3
    READY           = 4

Old=OldVerslagStatus
New=VerslagStatus
translation= {
    Old.NEW_MULTIPLE: New.NEW_MULTIPLE,
    Old.NEEDS_GRADING: New.NEEDS_GRADING,
    }

def modify_verslag_status(database: Database):
    print('modifying VERSLAGEN table.')
    database.drop_view(oldStudentVerslagenOverzichtDefinition()) # to be sure, will be restored in add_views
    database._execute_sql_command('alter table VERSLAGEN RENAME TO OLD_VERSLAGEN')
    print('creating the new table')
    verslagen_table = VerslagenTableDefinition() 
    database.execute_sql_command(SQLcreateTable(verslagen_table))
    #copying the data
    database._execute_sql_command('insert into VERSLAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer)'+ \
                                  ' select id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer from OLD_VERSLAGEN', [])

    print('implementing new Status values for VERSLAGEN.')
    for row in database._execute_sql_command(f'select id, status from VERSLAGEN WHERE status in ({",".join(["?"] * len(translation.keys()))})', 
                                                list(translation.keys()), True):
        database._execute_sql_command('update VERSLAGEN set status=? where id=?', [translation[row['status']], row['id']]) 
    print('end modifying new Status values for VERSLAGEN.')
    database._execute_sql_command('drop table OLD_VERSLAGEN')
    print('end modifying VERSLAGEN table.')

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
    modify_table(database, UndoLogsTableDefinition(), _copy_undolog_data)    
    # add new UNDOLOG_VERSLAGEN table    
    database.execute_sql_command(SQLcreateTable(UndoLogVerslagenTableDefinition()))  
    print('ready')    

def add_views(database: Database):
    print('modify view STUDENT_VERSLAGEN_OVERZICHT')
    database.drop_view(oldStudentVerslagenOverzichtDefinition())
    database.execute_sql_command(SQLcreateView(oldStudentVerslagenOverzichtDefinition()))    
    print('ready ')

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_verslag_status(database)
        modify_undo_logs(database)
        delete_verslagen(database)
        add_views(database)
        M124JsonData().execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
        
         # 