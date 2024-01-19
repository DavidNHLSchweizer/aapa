from pathlib import Path
import data.aapa_database as db
from database.database import Database
from data.storage.aapa_storage import AAPAStorage
from general.fileutil import file_exists
from general.log import log_error

class AAPAInitializationError(Exception):pass
def __create_database(name, recreate = False, ignore_version=False, onedrive_root=None)->Database:
    try:
        exists = file_exists(name)
        basename = Path(name).name
        if recreate or not exists:
            action = 'REINITIALISATIE' if exists else 'INITIALISATIE nieuwe'
            print(f'--- {action} DATABASE {basename} ---')
            result = db.AAPaDatabase.create_from_schema(db.AAPaSchema(), name, onedrive_root=onedrive_root)
            return result
        else:
            print(f'--- OPENEN DATABASE {basename} ---')
            return  db.AAPaDatabase(name, ignore_version=ignore_version, onedrive_root=onedrive_root)
    except AAPAInitializationError as Mystery:
        log_error(f'Fout bij opstarten: {Mystery}')
        return None
def initialize_database(database_name, recreate = False, ignore_version=False, onedrive_root=None)->Database:
    return __create_database(database_name, recreate, ignore_version=ignore_version, onedrive_root=onedrive_root)

def initialize_storage(database: Database)->AAPAStorage:
    return AAPAStorage(database)
