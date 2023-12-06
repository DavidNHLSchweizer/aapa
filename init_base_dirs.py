from data.aapa_database import DBVERSION
from data.migrate.migrate import init_database
from data.migrate.migrate_119_120 import init_base_directories
from database.database import Database
from general.log import init_logging

def prepare(database_name: str)->Database:
    init_logging(f'base_directories.log', debug=True)    
    if not (database := init_database(database_name, DBVERSION)):
        return None
    print(f'Adding basedirs to database {database_name}.')
    return database

if __name__ == "__main__":
    database_name = 'vesting123.db'
    init_base_directories(prepare(database_name))