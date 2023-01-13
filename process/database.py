from pathlib import Path
import data.AAPdatabase as db
from database.database import Database
from data.storage import AAPStorage

def __create_database(name, recreate = False)->Database:
    exists = Path(name).is_file()
    if recreate or not exists:
        action = 'REINITIALISATIE' if exists else 'INITIALISATIE'
        print(f'--- {action} DATABASE {name} ---')
        return  db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
    else:
        print(f'--- OPENEN DATABASE {name} ---')
        return  db.AAPDatabase(name)

def initialize_database(database_name, recreate = False)->Database:
    return __create_database(database_name, recreate)

def initialize_storage(database: Database)->AAPStorage:
    return AAPStorage(database)
