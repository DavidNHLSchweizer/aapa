from enum import IntEnum
from database.aapa_database import ActionLogFilesTableDefinition
from data.classes.files import File
from database.classes.sql_table import SQLcreateTable
from database.classes.database import Database
from database.classes.table_def import ForeignKeyAction
from data.classes.aanvragen import Aanvraag

# Wijzigingen in 1.18 voor migratie:
#
# hernummeren File.Type GRADE_FORM_PDF
# nieuwe tabel ACTIONLOG_FILES (voorloper op uitbreiding UNDO)
# correcties voor veranderingen in root directory 

def update_filetypes(database: Database):
    class OldFileType(IntEnum):
        INVALID_PDF         = -2
        UNKNOWN             = -1
        AANVRAAG_PDF        = 0
        GRADE_FORM_DOCX     = 1
        COPIED_PDF          = 2
        DIFFERENCE_HTML     = 3
        GRADE_FORM_PDF      = 5
    Old = OldFileType
    New = File.Type
    print('updating filetypes in FILES table.')
    new_filetype= {Old.GRADE_FORM_PDF:New.GRADE_FORM_PDF, }
    for row in database._execute_sql_command('select filetype, filename from FILES WHERE filetype in (?)', 
                                            [Old.GRADE_FORM_PDF, ], 
                                            True):
        database._execute_sql_command('update FILES set filetype=? where filename=?', [new_filetype[row['filetype']], row['filename']]) 
    print('end updating filetypes in FILES table.')

def create_new_tables(database: Database):
    print('toevoegen nieuwe tabel ACTIONLOG_FILES')
    action_log_files_table = ActionLogFilesTableDefinition()        
    action_log_files_table.add_foreign_key('log_id', 'ACTIONLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    action_log_files_table.add_foreign_key('file_id', 'FILES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreateTable(action_log_files_table))
    print('--- klaar toevoegen nieuwe tabellen')

def migrate_database(database: Database):
    update_filetypes(database)
    create_new_tables(database)

