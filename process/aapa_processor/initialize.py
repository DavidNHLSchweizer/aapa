from pathlib import Path
import data.AAPdatabase as db
from database.database import Database
from data.storage import AAPStorage

def __create_database(name, recreate = False)->Database:
    exists = Path(name).is_file()
    basename = Path(name).name
    if recreate or not exists:
        action = 'REINITIALISATIE' if exists else 'INITIALISATIE nieuwe'
        print(f'--- {action} DATABASE {basename} ---')
        result = db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
        return result
    else:
        print(f'--- OPENEN DATABASE {basename} ---')
        return  db.AAPDatabase(name)

def initialize_database(database_name, recreate = False)->Database:
    return __create_database(database_name, recreate)

def initialize_storage(database: Database)->AAPStorage:
    return AAPStorage(database)
