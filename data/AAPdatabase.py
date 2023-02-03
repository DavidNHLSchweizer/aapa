from database.tabledef import ForeignKeyAction, TableDefinition
from database.database import Database, Schema
import database.dbConst as dbc
from general.keys import reset_key
from general.config import config
from general.log import logError, logInfo, logWarning
from general.versie import Versie
from data.roots import add_root, get_roots, get_roots_report, reset_roots

class AAPaException(Exception): pass

DBVERSION = '1.14'
class DBVersie(Versie):
    def __init__(self, db_versie = DBVERSION, **kwargs):
        super().__init__(**kwargs)
        self.db_versie = db_versie

def init_config():
    config.set_default('database', 'database_name','aapa.DB')
    config.set('database', 'db_versie', DBVERSION)
init_config()

class VersionTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('VERSIE', autoid=True)
        self.add_column('db_versie', dbc.TEXT)
        self.add_column('versie', dbc.TEXT)
        self.add_column('datum', dbc.TEXT)

def read_version_info(database: Database)->DBVersie:
    if row := database._execute_sql_command('select id, db_versie, versie, datum from versie order by id desc', [], True):
        record = row[0]
        return DBVersie(db_versie = record['db_versie'], versie=record['versie'], datum=record['datum'])
    else:
        return DBVersie(db_versie = config.get('database', 'versie'), versie=config.get('versie', 'versie'), datum=Versie.datetime_str())

def create_version_info(database: Database, versie: DBVersie): 
    database._execute_sql_command('insert into versie (db_versie, versie, datum) values (?,?,?)', [versie.db_versie, versie.versie, versie.datum])
    database.commit()

class FileRootTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILEROOT', autoid=True)
        self.add_column('code', dbc.TEXT)
        self.add_column('root', dbc.TEXT)

def create_root(database: Database, code, root: str):
    database._execute_sql_command('insert into fileroot (code, root) values (?,?);', [code, root])
    database.commit()

def create_roots(database: Database):
    for code,root in get_roots():
        create_root(database, code, root)        
            
def load_roots(database: Database):
    reset_roots()
    if row := database._execute_sql_command('select code, root from fileroot', [], True): 
        for record in row:            
            add_root(record['root'], record['code']) 
            

class StudentTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENTEN')
        self.add_column('stud_nr', dbc.TEXT, primary=True)
        self.add_column('full_name', dbc.TEXT)
        self.add_column('first_name', dbc.TEXT)
        self.add_column('email', dbc.TEXT)
        self.add_column('tel_nr', dbc.TEXT)

class BedrijfTableDefinition(TableDefinition):
    KEY_FOR_ID = 'Bedrijf' # key in general.keys used to generate IDs
    def __init__(self):
        super().__init__('BEDRIJVEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('name', dbc.TEXT)    

class AanvraagTableDefinition(TableDefinition):
    KEY_FOR_ID  = 'Aanvraag' 
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_nr', dbc.TEXT)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('titel', dbc.TEXT)
        self.add_column('aanvraag_nr', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_column('beoordeling', dbc.INTEGER)

class FileTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('filename', dbc.TEXT, primary=True)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        self.add_column('aanvraag_id', dbc.INTEGER)

class AAPSchema(Schema):
    def __init__(self):
        super().__init__()
        self.add_table(VersionTableDefinition())
        self.add_table(FileRootTableDefinition())
        self.add_table(StudentTableDefinition())
        self.add_table(BedrijfTableDefinition())
        self.add_table(AanvraagTableDefinition())
        self.add_table(FileTableDefinition())
        self.__define_foreign_keys()
    def __define_foreign_keys(self):
        self.table('AANVRAGEN').add_foreign_key('stud_nr', 'STUDENTEN', 'stud_nr', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.table('AANVRAGEN').add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

        # de volgende Foreign Key ligt voor de hand. Er kunnen echter ook niet-aanvraag-gelinkte files zijn (FileType.InvalidPDF) die om efficientieredenen toch worden opgeslagen
        # (dan worden ze niet steeds opnieuw ingelezen). De eenvoudigste remedie is om de foreign key te laten vervallen. 
        #
        # self.table('FILES').add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        #
        # TODO: Je zou nog kunnen overwegen een check te doen bij de aanmaak. Als er een INSERT of UPDATE is met een invalid aanvraag_id (trigger) kan je een exception raisen. 
        # Dit is wel ingewikkeld, want moet ook op de AANVRAGEN tabel (on DELETE) worden gechecked. Voorlopig werkt het zo waarschijnlijk ook wel.
        # Andere oplossing: een "lege" aanvraag opslaan en daarnaar verwijzen. Kan weer andere problemen veroorzaken, maar als het kan worden opgevangen in storage.py is het misschien 
        # toch de netste oplossing.

class AAPDatabase(Database):
    def __init__(self, filename, _reset_flag = False):
        super().__init__(filename, _reset_flag)
        self.schema = Schema()
        self.schema.read_from_database(self)        
        if not self._reset_flag:
            self.reset_keys()
            self.check_version(False)
            self.load_roots(False)
    def reset_keys(self):
        reset_key(BedrijfTableDefinition.KEY_FOR_ID, self.__find_max_key('BEDRIJVEN'))
        reset_key(AanvraagTableDefinition.KEY_FOR_ID, self.__find_max_key('AANVRAGEN'))
    def __find_max_key(self, table_name: str):
        if (row := self._execute_sql_command(f'select max(ID) from {table_name};', return_values = True)) and \
                                            (r0 := list(row[0])[0]):
            return r0 
        else:
            return 0
    @classmethod
    def create_from_schema(cls, schema: Schema, filename: str):
        result = super().create_from_schema(schema, filename)
        result.check_version(True)
        result.load_roots(True)
        return result
    def __version_error(self, db_versie, errorStr):
        logError (errorStr)
        raise AAPaException()
    def check_version(self, recreate = False):
        logInfo('--- Controle versies database en programma')
        try:
            if recreate:
                create_version_info(self, DBVersie(db_versie=config.get('database', 'db_versie'), versie=config.get('versie', 'versie'), datum=Versie.datetime_str()))
            else:
                versie = read_version_info(self)
                if  versie.db_versie != config.get('database', 'db_versie'):
                    self.__version_error(versie.db_versie, f"Database version {versie.db_versie} does not match current program (expected {config.get('database', 'db_versie')}).")
                elif versie.versie != config.get('versie', 'versie'):
                    logWarning(f"Program version ({config.get('versie', 'versie')}) does not match version in database (expected {versie.versie}). Updating database en configuratie.")
                    versie.versie = config.get('versie', 'versie')
                    versie.datum = Versie.datetime_str()
                    create_version_info(self, versie)
                    config.set('versie', 'versie', versie.versie)
                    config.set('versie', 'datum', versie.datum)
            logInfo('--- Einde controle versies database en programma')
        except AAPaException as E:
            logError('This version of the program can not open this database. Use -init or migrate the data to the new database structure.')
    def load_roots(self, recreate = False):
        logInfo('--- Laden paden voor File Encoding')
        if recreate:
            create_roots(self)
        else:
            load_roots(self)
        logInfo(f'Bekende paden:\n{get_roots_report()}')
        logInfo('--- Einde laden paden File Encoding')
