from enum import IntEnum
from data.AAPdatabase import ProcessLogAanvragenTableDefinition, ProcessLogTableDefinition
from data.classes.files import File
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction

# Wijzigingen in 1.17 voor migratie:
#
# toevoegen PROCESSLOG en PROCESSLOG_AANVRAGEN tabel
# hernummeren File.Type constantes
#
def create_new_tables(database: Database):
    print('toevoegen nieuwe tabellen PROCESSLOG en PROCESSLOG_AANVRAGEN')
    database.execute_sql_command(SQLcreate(ProcessLogTableDefinition()))
    progress_log_aanvragen_table = ProcessLogAanvragenTableDefinition()        
    progress_log_aanvragen_table.add_foreign_key('log_id', 'PROCESSLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    progress_log_aanvragen_table.add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(progress_log_aanvragen_table))
    print('--- klaar toevoegen nieuwe tabellen')

class OldFileType(IntEnum):
    UNKNOWN             = -1
    AANVRAAG_PDF        = 0
    INVALID_PDF         = 1
    TO_BE_GRADED_DOCX   = 2
    GRADED_DOCX         = 3
    GRADED_PDF          = 4
    COPIED_PDF          = 5
    DIFFERENCE_HTML     = 6

def update_filetypes(database: Database):
    print('updating filetypes in FILES table.')
    new_filetype= {OldFileType.INVALID_PDF:File.Type.INVALID_PDF, 
                   OldFileType.TO_BE_GRADED_DOCX:File.Type.TO_BE_GRADED_DOCX, 
                   OldFileType.GRADED_DOCX:File.Type.GRADED_DOCX, 
                   OldFileType.GRADED_PDF:File.Type.GRADED_PDF, 
                   OldFileType.COPIED_PDF:File.Type.COPIED_PDF, 
                   OldFileType.DIFFERENCE_HTML:File.Type.DIFFERENCE_HTML,
                   }
    for row in database._execute_sql_command('select filetype, filename from FILES WHERE filetype in (?,?,?,?,?,?)', 
                                            [OldFileType.INVALID_PDF, OldFileType.TO_BE_GRADED_DOCX, OldFileType.GRADED_DOCX, 
                                             OldFileType.GRADED_PDF, OldFileType.COPIED_PDF, OldFileType.DIFFERENCE_HTML,], 
                                             True):
        database._execute_sql_command('update FILES set filetype=? where filename=?', [new_filetype[row['filetype']], row['filename']]) 
    print('end updating filetypes in FILES table.')

def migrate_database(database: Database):
    create_new_tables(database)
    update_filetypes(database)

