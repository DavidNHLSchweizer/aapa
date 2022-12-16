from pathlib import Path
import data.AAPdatabase as db
from database.database import Database
from data.storage import AAPStorage
from general.config import config

def init_config():
    config.set_default('database', 'database_name','aapa.DB')
init_config()

def __create_database(name, recreate = False)->Database:
    exists = Path(name).is_file()
    if recreate or not exists:
        action = 'REINITIALISATIE' if exists else 'INITIALISATIE'
        print(f'--- {action} DATABASE {name} ---')
        return  db.AAPDatabase.create_from_schema(db.AAPSchema(), name)
    else:
        print(f'--- OPENEN DATABASE {name} ---')
        return  db.AAPDatabase(name)

def initialize_database(recreate = False)->Database:
    name = config.get('database', 'database_name')
    return __create_database(name, recreate)

def initialize_storage(database: Database)->AAPStorage:
    return AAPStorage(database)
