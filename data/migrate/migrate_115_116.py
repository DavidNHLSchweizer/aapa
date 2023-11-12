from enum import IntEnum
from data.AAPdatabase import AAPDatabase, FileRootTableDefinition
from data.classes.aanvragen import Aanvraag
from database.SQLtable import SQLcreateTable
from database.database import Database

def add_unique_constraint_to_fileroot(database: Database):
    print('adding UNIQUE constraint to FILEROOT table.')
    database._execute_sql_command('alter table FILEROOT RENAME TO OLD_FILEROOT')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(FileRootTableDefinition()))
    database._execute_sql_command('insert into FILEROOT select * from OLD_FILEROOT', [])
    database._execute_sql_command('drop table OLD_FILEROOT')
    print('end adding UNIQUE constraint to FILEROOT table.')

class OldAanvraagStatus(IntEnum):
    INITIAL         = 0
    NEEDS_GRADING   = 1
    GRADED          = 2
    MAIL_READY      = 3
    READY           = 4
    READY_IMPORTED  = 5
    ARCHIVED        = 6

def update_aanvraag_status(database: AAPDatabase):
    print('updating values in AANVRAGEN table.')
    new_status={OldAanvraagStatus.MAIL_READY:Aanvraag.Status.MAIL_READY, OldAanvraagStatus.READY:Aanvraag.Status.READY, 
                OldAanvraagStatus.READY_IMPORTED:Aanvraag.Status.READY_IMPORTED, OldAanvraagStatus.ARCHIVED:Aanvraag.Status.ARCHIVED}
    for row in database._execute_sql_command('select id,status from AANVRAGEN WHERE status in (?,?,?,?)', [OldAanvraagStatus.MAIL_READY,OldAanvraagStatus.READY,
                                                                                                           OldAanvraagStatus.READY_IMPORTED,OldAanvraagStatus.ARCHIVED], True):            
        database._execute_sql_command('update AANVRAGEN set status=? WHERE ID=?', [new_status[row['status']], row['id']]) 
    print('end updating values in AANVRAGEN table.')

def migrate_database(database: Database):  
    add_unique_constraint_to_fileroot()
    update_aanvraag_status(database)   
    
