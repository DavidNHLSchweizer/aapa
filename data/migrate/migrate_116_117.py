from enum import IntEnum
from data.AAPdatabase import ActionLogAanvragenTableDefinition, ActionLogTableDefinition
from data.classes.files import File
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction
from data.classes.aanvragen import Aanvraag

# Wijzigingen in 1.17 voor migratie:
#
# toevoegen ACTIONLOG en ACTIONLOG_AANVRAGEN tabel
# hernummeren File.Type constantes
#
def create_new_tables(database: Database):
    print('toevoegen nieuwe tabellen ACTIONLOG en ACTIONLOG_AANVRAGEN')
    database.execute_sql_command(SQLcreate(ActionLogTableDefinition()))
    action_log_aanvragen_table = ActionLogAanvragenTableDefinition()        
    action_log_aanvragen_table.add_foreign_key('log_id', 'ACTIONLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    action_log_aanvragen_table.add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(action_log_aanvragen_table))
    print('--- klaar toevoegen nieuwe tabellen')

def update_filetypes(database: Database):
    class OldFileType(IntEnum):
        UNKNOWN             = -1
        AANVRAAG_PDF        = 0
        INVALID_PDF         = 1
        TO_BE_GRADED_DOCX   = 2
        GRADED_DOCX         = 3
        GRADED_PDF          = 4
        COPIED_PDF          = 5
        DIFFERENCE_HTML     = 6
    Old = OldFileType
    New = File.Type

    print('updating filetypes in FILES table.')
    new_filetype= {Old.INVALID_PDF:New.INVALID_PDF, 
                   Old.TO_BE_GRADED_DOCX:New.GRADE_FORM_DOCX, 
                   Old.GRADED_DOCX:New.GRADE_FORM_DOCX, 
                   Old.GRADED_PDF:New.GRADE_FORM_PDF, 
                   Old.COPIED_PDF:New.COPIED_PDF, 
                   Old.DIFFERENCE_HTML:New.DIFFERENCE_HTML,
                   }
    for row in database._execute_sql_command('select filetype, filename from FILES WHERE filetype in (?,?,?,?,?,?)', 
                                            [Old.INVALID_PDF, Old.TO_BE_GRADED_DOCX, Old.GRADED_DOCX, 
                                             Old.GRADED_PDF, Old.COPIED_PDF, Old.DIFFERENCE_HTML,], 
                                             True):
        database._execute_sql_command('update FILES set filetype=? where filename=?', [new_filetype[row['filetype']], row['filename']]) 
    print('end updating filetypes in FILES table.')

def update_aanvraag_status(database: Database):
    class OldAanvraagStatus(IntEnum):
        INITIAL         = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        MAIL_READY      = 3
        READY           = 4
        READY_IMPORTED  = 5
        ARCHIVED        = 6
    Old = OldAanvraagStatus
    New = Aanvraag.Status

    print('updating values in AANVRAGEN table.')
    new_status={Old.INITIAL: New.IMPORTED_PDF, Old.NEEDS_GRADING: New.NEEDS_GRADING, Old.GRADED: New.GRADED, 
                Old.MAIL_READY: New.MAIL_READY, Old.READY: New.READY, Old.READY_IMPORTED: New.READY_IMPORTED, Old.ARCHIVED: New.ARCHIVED}
    for row in database._execute_sql_command('select id,status from AANVRAGEN', [], True):
        database._execute_sql_command('update AANVRAGEN set status=? WHERE ID=?', [new_status[row['status']], row['id']]) 
    print('end updating values in AANVRAGEN table.')




def migrate_database(database: Database):
    create_new_tables(database)
    update_filetypes(database)
    update_aanvraag_status(database)

