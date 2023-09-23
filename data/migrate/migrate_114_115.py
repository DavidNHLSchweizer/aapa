from pathlib import Path
from data.classes.files import File
from data.storage import AAPStorage
from database.database import Database

def migrate_database(database: Database):
    storage = AAPStorage(database)    
    print('adding DIGEST column to FILES table.')
    database._execute_sql_command('alter table FILES add DIGEST text')
    print('filling the column with data')
    rows = database._execute_sql_command('select filename from files', [], True)
    for row in rows:
        file = storage.files.read(row['filename'])
        if not file:
            f_name = row['filename']
            print(f'\tWARNING: "{f_name}" could not be loaded from database')
        elif not Path(file.filename).is_file():
            print(f'\tWARNING: "{file.filename}" does not exist')
        else:
            print(f'\t{file.filename}')
            file.digest = File.get_digest(file.filename)
            storage.files.update(file)
    print('end adding DIGEST column to FILES table.')
