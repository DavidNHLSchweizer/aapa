from pathlib import Path
from data.AAPdatabase import AAPDatabase, FileRootTableDefinition, create_version_info, read_version_info
from data.storage import AAPStorage
from data.classes import FileInfo
from database.SQL import SQLcreate
from database.database import Database
from process.aapa_processor.initialize import initialize_database

def init_database(database_name, expected_version):
    database = initialize_database(database_name, ignore_version=True)    
    dbv = read_version_info(database)
    if dbv.db_versie != expected_version:
       print(f'Database {database_name} heeft versie {dbv.db_versie}. Verwacht {expected_version}. Kan migratie niet uitvoeren.') 
       return None
    return database
def update_versie(database, new_version):
    dbv = read_version_info(database)
    dbv.db_versie = new_version
    create_version_info(database, dbv)

def migrate_version_114_115(database_name):
    if not (database := init_database(database_name, '1.14')):
        return
    print(f'Migrating database {database_name} from version 1.14 to 1.15.')
    storage = AAPStorage(database)    
    print('adding DIGEST column to FILES table.')
    database._execute_sql_command('alter table FILES add DIGEST text')
    print('filling the column with data')
    rows = database._execute_sql_command('select filename from files', [], True)
    for row in rows:
        info = storage.file_info.read(row['filename'])
        if not info:
            f_name = row['filename']
            print(f'\tWARNING: "{f_name}" could not be loaded from database')
        elif not Path(info.filename).is_file():
            print(f'\tWARNING: "{info.filename}" does not exist')
        else:
            print(f'\t{info.filename}')
            info.digest = FileInfo.get_digest(info.filename)
            storage.file_info.update(info)
    print('end adding DIGEST column to FILES table.')
    print('updating database versie')
    update_versie(database, '1.15')    
    storage.commit()

def migrate_version_115_116(database_name):
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
    
    if not (database := init_database(database_name, '1.15')):
        return
    print(f'Migrating database {database_name} from version 1.15 to 1.16.')
    # storage = AAPStorage(database)    
    add_unique_constraint_to_fileroot()
    update_aanvraag_status(database)
    # for row in rows:
    #     info = storage.file_info.read(row['filename'])
    #     if not info:
    #         f_name = row['filename']
    #         print(f'\tWARNING: "{f_name}" could not be loaded from database')
    #     elif not Path(info.filename).is_file():
    #         print(f'\tWARNING: "{info.filename}" does not exist')
    #     else:
    #         print(f'\t{info.filename}')
    #         info.digest = FileInfo.get_digest(info.filename)
    #         storage.file_info.update(info)
    
    print('updating database versie')
    update_versie(database, '1.16')    
    database.commit()

