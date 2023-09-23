from data.AAPdatabase import AAPDatabase, FileRootTableDefinition
from database.SQL import SQLcreate
from database.database import Database

def migrate_database(database: Database):
    def add_unique_constraint_to_fileroot():
        print('adding UNIQUE constraint to FILEROOT table.')
        database._execute_sql_command('alter table FILEROOT RENAME TO OLD_FILEROOT')
        print('creating the new table')
        database.execute_sql_command(SQLcreate(FileRootTableDefinition()))
        database._execute_sql_command('insert into FILEROOT select * from OLD_FILEROOT', [])
        database._execute_sql_command('drop table OLD_FILEROOT')
        print('end adding UNIQUE constraint to FILEROOT table.')
    def update_aanvraag_status(database: AAPDatabase):
        print('updating values in AANVRAGEN table.')
        new_status={3:4, 4:5, 5:6, 6:3}
        for row in database._execute_sql_command('select id,status from AANVRAGEN WHERE status in (?,?,?,?)', [3,4,5,6], True):            
            database._execute_sql_command('update AANVRAGEN set status=? WHERE ID=?', [new_status[row['status']], row['id']]) 
        print('end updating values in AANVRAGEN table.')
   
    add_unique_constraint_to_fileroot()
    update_aanvraag_status(database)   
    
