from data.AAPdatabase import ProcessLogAanvragenTableDefinition, ProcessLogTableDefinition
from database.SQL import SQLcreate
from database.database import Database
from database.tabledef import ForeignKeyAction

# Wijzigingen in 1.17 voor migratie:
#
# toevoegen PROCESSLOG en PROCESSLOG_AANVRAGEN tabel
# hernummeren FileType constantes
#
def create_new_tables(database: Database):
    print('toevoegen nieuwe tabellen PROCESSLOG en PROCESSLOG_AANVRAGEN')
    database.execute_sql_command(SQLcreate(ProcessLogTableDefinition()))
    progress_log_aanvragen_table = ProcessLogAanvragenTableDefinition()        
    progress_log_aanvragen_table.add_foreign_key('log_id', 'PROCESSLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    progress_log_aanvragen_table.add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    database.execute_sql_command(SQLcreate(progress_log_aanvragen_table))
    print('--- klaar toevoegen nieuwe tabellen')

def update_filetypes(database: Database):
    print('updating filetypes in FILES table.')
    new_filetype= {1:-2, 2:1, 3:4, 4:5, 5:2, 6:3}

    for row in database._execute_sql_command('select filetype, filename from FILES WHERE filetype in (?,?,?,?,?,?)', [1,2,3,4,5,6], True):
        database._execute_sql_command('update FILES set filetype=? where filename=?', [new_filetype[row['filetype']], row['filename']]) 
    print('end updating filetypes in FILES table.')

def migrate_database(database: Database):
    create_new_tables(database)
    update_filetypes(database)

