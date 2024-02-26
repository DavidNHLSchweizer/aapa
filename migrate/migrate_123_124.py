from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from data.general.const import VerslagStatus
from database.aapa_database import AanvraagDetailsTableDefinition, AanvragenFileOverzichtDefinition,AanvragenFileOverzichtDefinition, MijlpaalDirectoryDetailsTableDefinition,StudentDirectoryDetailsTableDefinition, StudentDirectoriesFileOverzichtDefinition,StudentMijlpaalDirectoriesOverzichtDefinition,StudentVerslagenOverzichtDefinition,  UndoLogsTableDefinition,  UndologDetailsTableDefinition, VerslagenTableDefinition, VerslagDetailsTableDefinition
from database.classes.sql_table import SQLcreateTable, SQLdropTable
from database.classes.sql_view import SQLcreateView, SQLdropView
from main.options import AAPAProcessingOptions
from migrate.m124.obsolete import AanvraagFilesTableDefinition, MijlpaalDirectory_FilesTableDefinition, StudentDirectory_DirectoriesTableDefinition, UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, UndoLogVerslagenTableDefinition, VerslagFilesTableDefinition, oldAanvragenFileOverzichtDefinition, oldStudentDirectoriesFileOverzichtDefinition, oldStudentMijlpaalDirectoriesOverzichtDefinition, oldStudentVerslagenOverzichtDefinition
from migrate.migrate import JsonData, modify_table
from database.classes.database import Database
import database.classes.dbConst as dbc
 
class M124JsonData(JsonData):
    class KEY(Enum):
        CREATE_VERSLAGEN = auto()  
        CORRECT_MP_DIRS = auto()
        ADD_ORPHAN_VERSLAGEN = auto()
        CORRECT_VERSLAGEN_DOUBLURES = auto()
    def __init__(self):
        super().__init__(r'migrate\m124')
        self.init_entries()
    def init_entries(self):
        self.add_entry(self.KEY.CORRECT_MP_DIRS,filename='correct_mp_dirs', phase=1, message ='correcting inconsistencies in mijlpaal_directories')
        self.add_entry(self.KEY.CREATE_VERSLAGEN,filename='create_verslagen', phase=2, message ='"re-engineering" verslagen update')
        self.add_entry(self.KEY.ADD_ORPHAN_VERSLAGEN,filename='add_orphan_verslagen', phase=3, message ='correcting verslagen without any files attached')
        # self.add_entry(self.KEY.CORRECT_VERSLAGEN_DOUBLURES,filename='correct_verslagen_doublures', phase=3, message ='correcting doublure verslagen')

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

#next part is the re-building of details vies
#om pragmatic reasons (plugins were written for old situation, not necess to rewrite)
#this is done after phase 3
def _drop_views(database: Database):
    database.execute_sql_command(SQLdropView(oldAanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentMijlpaalDirectoriesOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(AanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(StudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(StudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(StudentMijlpaalDirectoriesOverzichtDefinition()))
def _create_aanvragen(database: Database):
    database.execute_sql_command(SQLdropTable(AanvraagDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(AanvraagDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into AANVRAGEN_DETAILS(aanvraag_id,detail_id,class_code) select aanvraag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from AANVRAGEN_FILES')
def _create_mijlpaal_directories(database: Database):
    database.execute_sql_command(SQLdropTable(MijlpaalDirectoryDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(MijlpaalDirectoryDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into MIJLPAAL_DIRECTORIES_DETAILS(mp_dir_id,detail_id,class_code) select mp_dir_id,file_id,"{ClassCodes.classtype_to_code(File)}" from MIJLPAAL_DIRECTORY_FILES')     
def _create_student_directories(database: Database):
    database.execute_sql_command(SQLdropTable(StudentDirectoryDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(StudentDirectoryDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into STUDENT_DIRECTORIES_DETAILS(stud_dir_id,detail_id,class_code) select stud_dir_id,mp_dir_id,"{ClassCodes.classtype_to_code(MijlpaalDirectory)}" from STUDENT_DIRECTORY_DIRECTORIES')
def _create_undologs(database: Database):
    database.execute_sql_command(SQLdropTable(UndologDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(UndologDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,aanvraag_id,"{ClassCodes.classtype_to_code(Aanvraag)}" from UNDOLOGS_AANVRAGEN')
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,file_id,"{ClassCodes.classtype_to_code(File)}" from UNDOLOGS_FILES')
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,verslag_id,"{ClassCodes.classtype_to_code(Verslag)}" from UNDOLOGS_VERSLAGEN')
def _create_verslagen(database: Database):
    database.execute_sql_command(SQLdropTable(VerslagDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into VERSLAGEN_DETAILS(verslag_id,detail_id,class_code) select verslag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from VERSLAGEN_FILES')
def _drop_old_tables(database: Database):
    database.execute_sql_command(SQLdropTable(UndoLogAanvragenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogVerslagenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(VerslagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(MijlpaalDirectory_FilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(StudentDirectory_DirectoriesTableDefinition()))    
def _create_views(database: Database):
    database.execute_sql_command(SQLcreateView(AanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))

def migrate_after_phase_3(database: Database):
    _drop_views(database)
    _create_aanvragen(database)
    _create_mijlpaal_directories(database)
    _create_student_directories(database)
    _create_undologs(database)
    _create_verslagen(database)
    _drop_old_tables(database)
    _create_views(database)
    database.commit()

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        modify_verslag_status(database)
        modify_undo_logs(database)
        delete_verslagen(database)
        add_views(database)
        M124JsonData().execute(database, phase)
        if phase > 3:
            migrate_after_phase_3(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
        
         # 