""" migratie naar database v1.25

Aanpassingen database (Aggregation CRUD).

"""
from dataclasses import dataclass
from enum import Enum, auto
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from database.aapa_database import AanvraagDetailsTableDefinition, AanvragenFileOverzichtDefinition,AanvragenFileOverzichtDefinition, LastVersionViewDefinition, MijlpaalDirectoryDetailsTableDefinition,StudentDirectoryDetailsTableDefinition, StudentDirectoriesFileOverzichtDefinition,StudentMijlpaalDirectoriesOverzichtDefinition,StudentVerslagenOverzichtDefinition,   UndologDetailsTableDefinition, VerslagDetailsTableDefinition
from database.classes.sql_table import SQLcreateTable, SQLdropTable
from database.classes.sql_view import SQLcreateView, SQLdropView
from migrate.m124.obsolete import AanvraagFilesTableDefinition, MijlpaalDirectory_FilesTableDefinition, StudentDirectory_DirectoriesTableDefinition, UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, UndoLogVerslagenTableDefinition, VerslagFilesTableDefinition, oldAanvragenFileOverzichtDefinition, oldStudentDirectoriesFileOverzichtDefinition, oldStudentMijlpaalDirectoriesOverzichtDefinition, oldStudentVerslagenOverzichtDefinition
from migrate.migrate import JsonData
from database.classes.database import Database
 
class M125JsonData(JsonData):
    class KEY(Enum):
        CORRECT_VERSLAGEN_DOUBLURES = auto()
    def __init__(self):
        super().__init__(r'migrate\m125')
        self.init_entries()
    def init_entries(self):
        # self.add_entry(self.KEY.CORRECT_VERSLAGEN_DOUBLURES,filename='correct_verslagen_doublures', phase=3, message ='correcting doublure verslagen')
        pass

def drop_views(database: Database):
    database.execute_sql_command(SQLdropView(oldAanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentMijlpaalDirectoriesOverzichtDefinition()))
def create_aanvragen(database: Database):
    database.execute_sql_command(SQLdropTable(AanvraagDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(AanvraagDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into AANVRAGEN_DETAILS(aanvraag_id,detail_id,class_code) select aanvraag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from AANVRAGEN_FILES')
def create_mijlpaal_directories(database: Database):
    database.execute_sql_command(SQLdropTable(MijlpaalDirectoryDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(MijlpaalDirectoryDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into MIJLPAAL_DIRECTORIES_DETAILS(mp_dir_id,detail_id,class_code) select mp_dir_id,file_id,"{ClassCodes.classtype_to_code(File)}" from MIJLPAAL_DIRECTORY_FILES')     
def create_student_directories(database: Database):
    database.execute_sql_command(SQLdropTable(StudentDirectoryDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(StudentDirectoryDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into STUDENT_DIRECTORIES_DETAILS(stud_dir_id,detail_id,class_code) select stud_dir_id,mp_dir_id,"{ClassCodes.classtype_to_code(MijlpaalDirectory)}" from STUDENT_DIRECTORY_DIRECTORIES')
def create_undologs(database: Database):
    database.execute_sql_command(SQLdropTable(UndologDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(UndologDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,aanvraag_id,"{ClassCodes.classtype_to_code(Aanvraag)}" from UNDOLOGS_AANVRAGEN')
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,file_id,"{ClassCodes.classtype_to_code(File)}" from UNDOLOGS_FILES')
    database._execute_sql_command(
        f'INSERT into UNDOLOGS_DETAILS(log_id,detail_id,class_code) select log_id,verslag_id,"{ClassCodes.classtype_to_code(Verslag)}" from UNDOLOGS_VERSLAGEN')
def create_verslagen(database: Database):
    database.execute_sql_command(SQLdropTable(VerslagDetailsTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagDetailsTableDefinition()))
    database._execute_sql_command(
        f'INSERT into VERSLAGEN_DETAILS(verslag_id,detail_id,class_code) select verslag_id,file_id,"{ClassCodes.classtype_to_code(File)}" from VERSLAGEN_FILES')
def drop_old_tables(database: Database):
    database.execute_sql_command(SQLdropTable(UndoLogAanvragenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogVerslagenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(VerslagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(MijlpaalDirectory_FilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(StudentDirectory_DirectoriesTableDefinition()))    
def create_views(database: Database):
    database.execute_sql_command(SQLcreateView(AanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(LastVersionViewDefinition()))

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        drop_views(database)
        create_aanvragen(database)
        create_mijlpaal_directories(database)
        create_student_directories(database)
        create_undologs(database)
        create_verslagen(database)
        drop_old_tables(database)
        create_views(database)
        M125JsonData().execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
        
         # 