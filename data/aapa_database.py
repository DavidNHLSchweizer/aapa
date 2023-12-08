from __future__ import annotations
from database.sql_table import SQLselect
from database.table_def import ForeignKeyAction, TableDefinition
from database.database import Database, Schema
import database.dbConst as dbc
from database.view_def import ViewDefinition
from general.keys import reset_key
from general.config import config
from general.log import log_debug, log_error, log_info, log_warning
from general.versie import Versie
from data.roots import add_root, get_roots, reset_roots

class AAPaException(Exception): pass

DBVERSION = '1.20'
class DBVersie(Versie):
    def __init__(self, db_versie = DBVERSION, **kwargs):
        super().__init__(**kwargs)
        self.db_versie = db_versie

class VersionTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('VERSIE', autoid=True)
        self.add_column('db_versie', dbc.TEXT)
        self.add_column('versie', dbc.TEXT)
        self.add_column('datum', dbc.TEXT)

def read_version_info(database: Database)->DBVersie:
    if row := database._execute_sql_command('select * from VERSIE order by id desc', [], True):
        record = row[0]
        return DBVersie(db_versie = record['db_versie'], versie=record['versie'], datum=record['datum'])
    else:
        return DBVersie(db_versie = DBVERSION, versie=config.get('versie', 'versie'), datum=Versie.datetime_str())

def create_version_info(database: Database, versie: DBVersie): 
    database._execute_sql_command('insert into VERSIE (db_versie, versie, datum) values (?,?,?)', [versie.db_versie, versie.versie, versie.datum])
    database.commit()

class FileRootTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILEROOT', autoid=True)
        self.add_column('code', dbc.TEXT, unique=True)
        self.add_column('root', dbc.TEXT)

def create_root(database: Database, code, root: str):
    database._execute_sql_command('insert into FILEROOT (code, root) values (?,?);', [code, root])
    database.commit()

def create_roots(database: Database):
    for code,root in get_roots():
        create_root(database, code, root)        
            
def load_roots(database: Database):
    reset_roots()
    for row in database._execute_sql_command('select code, root from fileroot', [], True): 
        if row['code'] == ':ROOT1:':
            continue # first row is already loaded, this is the NHL Stenden BASEPATH
        add_root(row['root'], row['code']) 
            
class DetailTableDefinition(TableDefinition):
    def __init__(self, name: str, 
                 main_table_name: str, main_alias_id: str, 
                 detail_table_name: str, detail_alias_id: str):
        super().__init__(name)
        self.add_column(main_alias_id, dbc.INTEGER, primary = True)
        self.add_column(detail_alias_id, dbc.INTEGER, primary = True)  
        self.add_foreign_key(main_alias_id, main_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key(detail_alias_id, detail_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class StudentTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENTEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_nr', dbc.TEXT)
        self.add_column('full_name', dbc.TEXT)
        self.add_column('first_name', dbc.TEXT)
        self.add_column('email', dbc.TEXT, notnull=True)
        self.add_column('tel_nr', dbc.TEXT)

class BedrijfTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BEDRIJVEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('name', dbc.TEXT)    

class MilestoneTableDefinition(TableDefinition):
    #model voor AANVRAGEN en VERSLAGEN tabellen
    def __init__(self, name: str):
        super().__init__(name)
        self.add_column('id', dbc.INTEGER, primary = True) 
        self.add_column('datum', dbc.TEXT)
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('titel', dbc.TEXT)
        self.add_column('kans', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_column('beoordeling', dbc.INTEGER)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class AanvraagTableDefinition(MilestoneTableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('versie', dbc.INTEGER)

class VerslagTableDefinition(MilestoneTableDefinition):
    def __init__(self):
        super().__init__('VERSLAGEN')
        self.add_column('verslag_type', dbc.INTEGER)
        self.add_column('cijfer', dbc.TEXT)
        self.add_column('directory', dbc.TEXT)

class VerslagFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('VERSLAGEN_FILES', 
                         main_table_name='VERSLAGEN', main_alias_id='verslag_id',
                         detail_table_name='FILES', detail_alias_id='file_id')

#NOTE: een index op FILES (bijvoorbeeld op filename, filetype of digest) ligt voor de hand
# Bij onderzoek blijkt echter dat dit bij de huidige grootte van de database (1000 files) 
# geen noemenswaardige tijdswinst oplevert. Dit kan dus beter wachten.
# De functionaliteit is al geprogrammeerd, de code kan eenvoudig worden aangezet.
# er is dan wel nog eenmalig een database migratie nodig.
class FilesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('filename', dbc.TEXT)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('digest', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        # self.add_index('name_index', 'filename')
        # self.add_index('digest_index', 'digest')
        # self.add_index('name_digest_index', ['digest','name'])

class AanvraagFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN_FILES', 
                         main_table_name='AANVRAGEN', main_alias_id='aanvraag_id',
                         detail_table_name='FILES', detail_alias_id='file_id')

class UndoLogTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('description', dbc.TEXT)
        self.add_column('action', dbc.INTEGER)    
        self.add_column('user', dbc.TEXT)    
        self.add_column('date', dbc.DATE)   
        self.add_column('can_undo', dbc.INTEGER)

class UndoLogAanvragenTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS_AANVRAGEN', 
                         main_table_name='UNDOLOGS', main_alias_id='log_id', 
                         detail_table_name='AANVRAGEN', detail_alias_id='aanvraag_id')
       
class UndoLogFilesTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS_FILES', 
                         main_table_name='UNDOLOGS', main_alias_id='log_id', 
                         detail_table_name='FILES', detail_alias_id='file_id')
    
class BaseDirsTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BASEDIRS')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('year', dbc.INTEGER)
        self.add_column('period', dbc.TEXT)
        self.add_column('forms_version', dbc.TEXT)
        self.add_column('directory', dbc.TEXT)

class StudentDirectoryTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORY')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('directory', dbc.TEXT)
        self.add_column('basedir_id', dbc.INTEGER)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('basedir_id', 'BASEDIRS', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class StudentDirectoryAanvragenTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORY_AANVRAGEN', 
                         main_table_name='STUDENT_DIRECTORY', main_alias_id='stud_dir_id',
                         detail_table_name='AANVRAGEN', detail_alias_id='aanvraag_id')

class StudentDirectoryVerslagenTableDefinition(DetailTableDefinition):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORY_VERSLAGEN', 
                         main_table_name='STUDENT_DIRECTORY', main_alias_id='stud_dir_id',
                         detail_table_name='VERSLAGEN', detail_alias_id='verslag_id')

class AanvragenOverzichtDefinition(ViewDefinition):
    def __init__(self):
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        bedrijf = '(select name from BEDRIJVEN as B where B.ID = A.bedrijf_id) as bedrijf'
        beoordeling = '(case beoordeling when 0 then "" when 1 then "onvoldoende" when 2 then "voldoende" end) as beoordeling'
        super().__init__('AANVRAGEN_OVERZICHT', 
                         query=f'select id,{stud_name},datum,{bedrijf},titel,versie,kans,{beoordeling} from AANVRAGEN as A order by 2,3')
        
class AanvragenFileOverzichtDefinition(ViewDefinition):
    def __init__(self):
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        innerjoins = ' inner join AANVRAGEN_FILES as AF on A.ID=AF.aanvraag_id inner join FILES as F on F.ID=AF.file_id'
        super().__init__('AANVRAGEN_FILE_OVERZICHT', 
                         query=f'select A.id,{stud_name},titel, F.ID as file_id,F.filename as filename \
                                from AANVRAGEN as A {innerjoins} where F.filetype=0 order by 2')
        
class AAPaSchema(Schema):
    ALL_TABLES:list[TableDefinition] = [
        VersionTableDefinition,
        FileRootTableDefinition,
        StudentTableDefinition,
        BedrijfTableDefinition,
        AanvraagTableDefinition,
        AanvraagFilesTableDefinition,
        FilesTableDefinition,
        UndoLogTableDefinition,
        UndoLogAanvragenTableDefinition,
        UndoLogFilesTableDefinition,
        VerslagTableDefinition,
        VerslagFilesTableDefinition,
        BaseDirsTableDefinition,
        StudentDirectoryTableDefinition,      
        StudentDirectoryAanvragenTableDefinition,
        StudentDirectoryVerslagenTableDefinition,
    ]
    ALL_VIEWS:list[ViewDefinition]= [ 
                AanvragenOverzichtDefinition,
                AanvragenFileOverzichtDefinition,
                ]
    def __init__(self):
        super().__init__()
        for tabledef in self.ALL_TABLES:
            self.add_table(tabledef())
        for viewdef in self.ALL_VIEWS:
            self.add_view(viewdef())

class AAPaDatabase(Database):
    def __init__(self, filename, _reset_flag = False, ignore_version=False):
        super().__init__(filename, _reset_flag)
        self.schema = Schema.read_from_database(self)  
        if not self._reset_flag: 
            version_correct = self.check_version(recreate=False,ignore_error=ignore_version)
            if version_correct:
                self.load_file_roots(False)
                self.reset_keys()
    def reset_keys(self):
        def is_keyed_table(table: TableDefinition)->bool:
            return len(table.keys) == 1 and table.column(table.key).type==dbc.INTEGER and table.key == 'id' 
        # keyed_tables:list[TableDefinition] = [AanvraagTableDefinition(), VerslagTableDefinition(), UndoLogTableDefinition(), BedrijfTableDefinition(), FilesTableDefinition()]
        for table in self.schema.tables():            
            if is_keyed_table(table):
                reset_key(table.name, self.__find_max_key(table.name))
    def __find_max_key(self, table_name: str):
        sql = SQLselect(self.schema.table(table_name), columns=['max(id)'])
        if rows := self.execute_select(sql):
            r = rows[0][0]            
            return r if r else 0
        # if (row := self._execute_sql_command(f'select max(ID) from {table_name};', return_values = True)) and \
        #                                     (r0 := list(row[0])[0]):
        #     return r0 
        else:
            return 0
    @classmethod
    def create_from_schema(cls, schema: Schema, filename: str):
        result = super().create_from_schema(schema, filename)
        if result:
            result.check_version(recreate=True)
            result.load_file_roots(True)
            result.reset_keys()
        return result
    def __version_error(self, db_versie, errorStr):
        log_error(errorStr)
        raise AAPaException()
    def check_version(self, recreate=False, ignore_error=False)->bool:
        log_info('--- Controle versies database en programma')
        result = True
        try:
            if recreate:
                create_version_info(self, DBVersie(db_versie=DBVERSION, versie=config.get('versie', 'versie'), datum=Versie.datetime_str()))
            else:
                versie = read_version_info(self)
                if versie.db_versie != DBVERSION:
                    result = False
                    if not ignore_error:
                        self.__version_error(versie.db_versie, f"Database versie {versie.db_versie} komt niet overeen met verwachte versie in programma (verwacht: {DBVERSION}).")
                elif versie.versie != config.get('versie', 'versie') and not ignore_error:
                    log_warning(f"Programma versie ({config.get('versie', 'versie')}) komt niet overeen met versie in database (verwacht: {versie.versie}).\nDatabase en configuratie worden bijgewerkt.")
                    versie.versie = config.get('versie', 'versie')
                    versie.datum = Versie.datetime_str()
                    create_version_info(self, versie)
                    config.set('versie', 'versie', versie.versie)
                    config.set('versie', 'datum', versie.datum)
            log_info('--- Einde controle versies database en programma')
            return result
        except AAPaException as E:
            if not ignore_error:
                log_error('Deze versie van het programma kan deze database niet openen.\nGebruik commando "new" of migreer de data naar de juiste databaseversie.')
                raise E
    def load_file_roots(self, recreate = False):
        log_info('--- Laden paden voor File Encoding')
        if recreate:
            create_roots(self)
        else:
            load_roots(self)
        report = '\n'.join([f'{code} = "{root}"' for (code,root) in get_roots()])
        log_info(f'Bekende paden:\n{report}')
        log_info('--- Einde laden paden File Encoding')


        
