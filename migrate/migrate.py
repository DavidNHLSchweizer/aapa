import importlib
from typing import Protocol
from database.aapa_database import AAPaSchema, create_version_info, read_version_info
from database.classes.database import Database
from database.classes.sql_table import SQLcreateTable
from database.classes.table_def import TableDefinition
from general.fileutil import file_exists
from main.log import init_logging
from process.main.initialize import initialize_database

class MigrationException(Exception): pass

def _remove_dot(s: str)->str:
    return s.replace('.', '')    

def migrate_version(database_name, old_version, new_version, debug=False, phase=42)->bool:    
    migration_module_name = f'migrate.migrate_{_remove_dot(old_version)}_{_remove_dot(new_version)}'
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
        if phase < 42:
            print(f'--- Migratie fase: {phase} ---')
        migrate_database(database, phase=phase)
        finish_migratie(database, new_version)    
        if (after_migrate:= getattr(module, 'after_migrate', None)): # to be refined later
            after_migrate(database_name, debug=debug, phase=phase)
    except Exception as E:
        print(f'Fout bij migratie {migration_module_name}: {E}')
        return False
    return True

def init_database(database_name, expected_version, actie='migratie'):
    if not file_exists(database_name):
        raise MigrationException(f'Database file {database_name} bestaat niet. {actie.capitalize()} niet mogelijk.')        
    database = initialize_database(database_name, recreate=False, ignore_version=True)    
    dbv = read_version_info(database)
    if dbv.db_versie != expected_version:
       print(f'Database {database_name} heeft versie {dbv.db_versie}. Verwacht {expected_version}. Kan {actie} niet uitvoeren.') 
       return None
    return database

def update_versie(database, new_version):
    dbv = read_version_info(database)
    dbv.db_versie = new_version
    create_version_info(database, dbv)

def start_migratie(database_name: str, old_version: str, new_version: str, debug=False)->Database:
    def underscorify(s: str, replace_chars: str=".  	")->str:
        result = s
        for char in replace_chars:
            result = result.replace(char,'_')
        return result
    init_logging(f'migrate{underscorify(old_version)}-{underscorify(new_version)}.log', debug=debug)    
    if not (database := init_database(database_name, old_version)):
        return None
    print(f'Migrating database {database_name} from version {old_version} to {new_version}.')
    return database

def finish_migratie(database: Database, new_version: str):
    print(f'Klaar!\nUpdating database version to {new_version}')
    update_versie(database, new_version)    
    database.commit()
    dump_file = f'.\\migrate\\schema_{_remove_dot(new_version)}.sql'
    AAPaSchema.dump_schema_sql(filename=dump_file)
    print(f'New schema dumped to {dump_file}.')

class copy_func(Protocol):
    def __call__(database:Database, old_table_name: str, new_table_name: str)->bool:pass

def modify_table(database: Database, new_table: TableDefinition, copy_data: copy_func):
    old_table_name = f'OLD_{new_table.name}'
    database._execute_sql_command(f'alter table {new_table.name} rename to {old_table_name}')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(new_table))
    if copy_data is None or copy_data(database, old_table_name, new_table.name):
        database._execute_sql_command(f'drop table {old_table_name}')
