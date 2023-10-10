from enum import IntEnum
from data.AAPdatabase import ActionLogAanvragenTableDefinition, ActionLogTableDefinition, FilesTableDefinition
from data.classes.files import File
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction
from data.classes.aanvragen import Aanvraag

# Wijzigingen in 1.18 voor migratie:
#
# hernummeren File.Type GRADE_FORM_PDF

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

def migrate_database(database: Database):
    update_filetypes(database)

