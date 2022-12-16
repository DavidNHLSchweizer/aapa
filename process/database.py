from pathlib import Path
import data.AAPdatabase as db
from database.database import Database
from storage import AAPStorage

def __create_database(name, recreate = False)->Database:
    if recreate or not Path(name).is_file():
        print('--- HERBOUW DATABASE ---')
        return  db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
    else:
        print('--- OPENEN DATABASE ---')
        return  db.AAPDatabase(name)

def initialize_database(DBNAME: str, recreate = False)->Database:
    return __create_database(DBNAME, recreate)

def initialize_storage(database: Database)->AAPStorage:
    return AAPStorage(database)
