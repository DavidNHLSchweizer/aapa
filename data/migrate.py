from pathlib import Path
from data.AAPdatabase import create_version_info, read_version_info
from data.storage import AAPStorage
from data.classes import FileInfo
from process.initialize import initialize_database

def init_database(database_name, expected_version):
    database = initialize_database(database_name)    
    dbv = read_version_info(database)
    if dbv.db_versie != expected_version:
       print(f'Database {database_name} is at version {dbv.db_versie}. Expected {expected_version}. Can not migrate.') 
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

