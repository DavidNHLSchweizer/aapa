import datetime
from pathlib import Path
import data.AAPdatabase as db
from database.database import Database
from data.storage import AAPStorage
from general.config import config
from general.versie import Versie

def init_config():
    config.set_default('database', 'database_name','aapa.DB')
    config.set_default('versie', 'db_versie', '1.0')
    config.set_default('versie', 'versie', '0.76')
    config.set_default('versie', 'datum', Versie.datetime_str(datetime.datetime.now()))
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

def initialize_database(database_name, recreate = False)->Database:
    database = __create_database(database_name, recreate)
    if recreate:
        database._execute_sql_command('insert into versie (db_versie,versie,datum) values (?,?,?)', [config.get('versie', 'db_versie'), config.get('versie', 'versie'), Versie.datetime_str(datetime.datetime.now())])
        database.commit()
    return database

def initialize_storage(database: Database)->AAPStorage:
    return AAPStorage(database)
