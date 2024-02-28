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
from database.aapa_database import AanvraagDetailsTableDefinition, AanvragenFileOverzichtDefinition,AanvragenFileOverzichtDefinition, LastVersionViewDefinition, MijlpaalDirectoriesTableDefinition, MijlpaalDirectoryDetailsTableDefinition,StudentDirectoryDetailsTableDefinition, StudentDirectoriesFileOverzichtDefinition,StudentMijlpaalDirectoriesOverzichtDefinition,StudentVerslagenOverzichtDefinition,   UndologDetailsTableDefinition, VerslagDetailsTableDefinition
from database.classes.sql_table import SQLcreateTable, SQLdropTable
from database.classes.sql_view import SQLcreateView, SQLdropView
from migrate.m124.obsolete import AanvraagFilesTableDefinition, MijlpaalDirectory_FilesTableDefinition, StudentDirectory_DirectoriesTableDefinition, UndoLogAanvragenTableDefinition, UndoLogFilesTableDefinition, UndoLogVerslagenTableDefinition, VerslagFilesTableDefinition, oldAanvragenFileOverzichtDefinition, oldStudentDirectoriesFileOverzichtDefinition, oldStudentMijlpaalDirectoriesOverzichtDefinition, oldStudentVerslagenOverzichtDefinition
from migrate.migrate import JsonData, modify_table
from database.classes.database import Database
 
class M125JsonData(JsonData):
    class KEY(Enum):
        CORRECT_FILES_DOUBLURES = auto()
        CORRECT_MISSING_AANVRAGEN_FILES = auto()
        CORRECT_FILES_IN_WEEK = auto()
        ADD_AANVRAGEN_TO_MP_DIRS= auto()
        ADD_VERSLAGEN_TO_MP_DIRS= auto()
        CORRECT_VERSLAGEN_DOUBLURES = auto()
    def __init__(self):
        super().__init__(r'migrate\m125')
        self.init_entries()
    def init_entries(self):
        self.add_entry(self.KEY.CORRECT_FILES_DOUBLURES,filename='correct_files_doublures', phase=1, message ='correcting doublures files')
        self.add_entry(self.KEY.CORRECT_MISSING_AANVRAGEN_FILES,filename='correct_missing_aanvragen_files',phase=1,message='Corrigeren aanvragen zonder gekoppelde bestanden')
        self.add_entry(self.KEY.CORRECT_FILES_IN_WEEK,filename='correct_files_in_week',phase=2,message='Corrigeren aanvragen met files die alleen op de "verkeerde" plaats staan')
        self.add_entry(self.KEY.CORRECT_VERSLAGEN_DOUBLURES,filename='correct_verslagen_doublures', phase=2, message ='correcting doublure verslagen')
        self.add_entry(self.KEY.ADD_AANVRAGEN_TO_MP_DIRS,filename='add_aanvragen_to_mp_dirs',phase=3,
                       message='Toevoegen aanvragen aan mijlpaal directories')
        self.add_entry(self.KEY.ADD_VERSLAGEN_TO_MP_DIRS,filename='add_verslagen_to_mp_dirs',phase=3,
                       message='Toevoegen verslagen aan mijlpaal directories')
        

def drop_views(database: Database):
    print('Dropping old views')
    database.execute_sql_command(SQLdropView(oldAanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLdropView(oldStudentMijlpaalDirectoriesOverzichtDefinition()))
    print('end dropping old views')

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

def create_new_tables(database: Database):
    print('creating and initializing new detail tables')
    create_aanvragen(database)
    create_mijlpaal_directories(database)
    create_student_directories(database)
    create_undologs(database)
    create_verslagen(database)
    print('end creating and initializing new detail tables')

def drop_old_tables(database: Database):
    print('Dropping old tables')
    database.execute_sql_command(SQLdropTable(UndoLogAanvragenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogVerslagenTableDefinition()))
    database.execute_sql_command(SQLdropTable(UndoLogFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(VerslagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(AanvraagFilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(MijlpaalDirectory_FilesTableDefinition()))
    database.execute_sql_command(SQLdropTable(StudentDirectory_DirectoriesTableDefinition()))    
    print('End dropping old tables')

def create_views(database: Database):
    print('Creating new views')
    database.execute_sql_command(SQLcreateView(AanvragenFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentVerslagenOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentMijlpaalDirectoriesOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(LastVersionViewDefinition()))
    print('end creating new views')

def _copy_mijlpaal_data(database: Database, old_table_name: str, new_table_name: str)->bool:
    print('copying data') 
    select = f'SELECT id,mijlpaal_type,kans,directory,datum FROM {old_table_name}'
    database._execute_sql_command(f'INSERT INTO {new_table_name}(id,mijlpaal_type,kans,directory,datum) {select}')
    print('ready')
    return True

def modify_mijlpaal_directories(database: Database):
    print('adding UNIQUE constraint on directory for mijlpaal_directories')
    modify_table(database, MijlpaalDirectoriesTableDefinition(), _copy_mijlpaal_data)    
    print('end adding UNIQUE constraint on directory for mijlpaal_directories')

def _correct_path(database: Database, table: str, path_column: str, path_to_correct_pattern: str, replace: str, replace_with: str):
    rows = database._execute_sql_command(f'select id,{path_column} from {table} where {path_column} like ?', [path_to_correct_pattern],True)    
    for row in rows:
        new_path = str(row[path_column]).replace(replace, replace_with)
        database._execute_sql_command(f'update {table} set {path_column}=? where id=?', [new_path, row['id']])

def _correct_path_2(database: Database, table: str, path_column: str, id: int, replace: str, replace_with: str):
    rows = database._execute_sql_command(f'select {path_column} from {table} where id = ?', [id],True)
    for row in rows:
        new_path = str(row[path_column]).replace(replace, replace_with)
        database._execute_sql_command(f'update {table} set {path_column}=? where id=?', [new_path, id])

def correct_filename_errors(database: Database):
    print('correcting filename errors/inconsistencies')
    #Ibrić, Elvedin
    database._execute_sql_command(f'UPDATE FILES SET FILENAME=? WHERE ID=?', [r':ROOT12:\Ibrić, Elvedin\Beoordeling afstudeeropdracht Elvedin.pdf',79])
    #Heij, de, Gerrit
    _correct_path(database, 'FILES', 'filename', r'%\Heij, de,Gerrit%',  "Heij, de,Gerrit", "Heij, de, Gerrit")
    #Micky Cheng
    _correct_path_2(database, 'MIJLPAAL_DIRECTORIES', 'directory', 591,  "onderzoeksverslag", "Onderzoeksverslag")
    print('end correcting filename errors/inconsistencies')
def _remove_missing_files(database: Database, table_name: str, main_id: str):
    file_code = ClassCodes.classtype_to_code(File)
    query = f'select DDD.detail_id from {table_name}_DETAILS as DDD inner join {table_name} as M on M.id=DDD.{main_id} where DDD.class_code = "{file_code}" and ' + \
    'not exists (select id from FILES as F where F.ID = DDD.detail_id)'
    file_ids = []
    for row in database._execute_sql_command(query,[], True):
        file_ids.append(row['detail_id'])
    commas = ",".join(['?']*len(file_ids))
    database._execute_sql_command(f'delete from {table_name}_DETAILS where detail_id in ({commas}) and class_code=="{file_code}"', file_ids)
    print(f'{table_name}: removed {file_ids}')
def remove_missing_files(database: Database):
    print('removing links to non-existent files from DETAILS-tables')
    _remove_missing_files(database, 'AANVRAGEN', 'aanvraag_id')
    _remove_missing_files(database, 'VERSLAGEN', 'verslag_id')
    _remove_missing_files(database, 'UNDOLOGS', 'log_id')
    _remove_missing_files(database, 'MIJLPAAL_DIRECTORIES', 'mp_dir_id')
    print(f'end removing links to non-existent files')
def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        drop_views(database)
        create_new_tables(database)
        drop_old_tables(database)
        modify_mijlpaal_directories(database)
        create_views(database)
        correct_filename_errors(database)
        remove_missing_files(database)
        M125JsonData().execute(database, phase)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.
        
         # 