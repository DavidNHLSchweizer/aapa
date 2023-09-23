from pathlib import Path
from data.classes.files import FileInfo
from data.storage import AAPStorage
from database.database import Database

def migrate_database(database: Database):
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
