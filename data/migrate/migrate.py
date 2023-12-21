import importlib
from data.aapa_database import create_version_info, read_version_info
from database.database import Database
from general.fileutil import file_exists
from general.log import init_logging
from process.aapa_processor.initialize import initialize_database

class MigrationException(Exception): pass

def migrate_version(database_name, old_version, new_version, debug=False, phase=42):    
    def remove_dot(s: str)->str:
        return s.replace('.', '')    
    migration_module_name = f'data.migrate.migrate_{remove_dot(old_version)}_{remove_dot(new_version)}'
    try:
        module = importlib.import_module(migration_module_name)
    except ModuleNotFoundError as E:
        print(E)
        return False       
    try:
        if not (migrate_database:= getattr(module, 'migrate_database', None)):
            print(f'Migration function "migrate_database" not found in {migration_module_name}.')
            return False
        if not (database := start_migratie(database_name, old_version, new_version, debug=debug)):
            return False
        migrate_database(database, phase=phase)
        finish_migratie(database, new_version)    
        if (after_migrate:= getattr(module, 'after_migrate', None)): # to be refined later
            after_migrate(database_name, debug=debug, phase=phase)
    except Exception as E:
        print(f'Fout bij migratie {migration_module_name}: {E}')
        return False
    return True

def init_database(database_name, expected_version):
    if not file_exists(database_name):
        raise MigrationException(f'Database file {database_name} bestaat niet. Migratie niet mogelijk.')
        
    database = initialize_database(database_name, recreate=False, ignore_version=True)    
    dbv = read_version_info(database)
    if dbv.db_versie != expected_version:
       print(f'Database {database_name} heeft versie {dbv.db_versie}. Verwacht {expected_version}. Kan migratie niet uitvoeren.') 
       return None
    return database

def update_versie(database, new_version):
    dbv = read_version_info(database)
    dbv.db_versie = new_version
    create_version_info(database, dbv)

def start_migratie(database_name: str, old_version: str, new_version: str, debug=False)->Database:
    init_logging(f'migrate{old_version.replace(".","_")}-{new_version.replace(".","_")}.log', debug=debug)    
    if not (database := init_database(database_name, old_version)):
        return None
    print(f'Migrating database {database_name} from version {old_version} to {new_version}.')
    return database

def finish_migratie(database: Database, new_version: str):
    print(f'Klaar!\nUpdating database version to {new_version}')
    update_versie(database, new_version)    
    database.commit()

