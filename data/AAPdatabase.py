from __future__ import annotations
from typing import Type
from database.SQLtable import SQLselect
from database.sqlexpr import SQE, Ops
from database.tabledef import ForeignKeyAction, TableDefinition
from database.database import Database, Schema
import database.dbConst as dbc
from database.viewdef import ViewDefinition
from general.keys import reset_key
from general.config import config
from general.log import log_error, log_info, log_warning
from general.versie import Versie
from data.roots import add_root, get_roots, get_roots_report, reset_roots

class AAPaException(Exception): pass

DBVERSION = '1.19'
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
    if row := database._execute_sql_command('select code, root from fileroot', [], True): 
        for record in row:   
            add_root(record['root'], record['code']) 
            
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
    def __init__(self):
        super().__init__('MILESTONES')
        self.add_column('id', dbc.INTEGER, primary = True) 
        self.add_column('milestone_type', dbc.INTEGER)
        self.add_column('datum', dbc.TEXT)
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('titel', dbc.TEXT)
        self.add_column('kans', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_column('beoordeling', dbc.TEXT)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class AanvraagTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('id', dbc.INTEGER, primary = True) 
        self.add_column('datum_str', dbc.TEXT)
        self.add_foreign_key('id', 'MILESTONES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class VerslagTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('VERSLAGEN')
        self.add_column('id', dbc.INTEGER, primary = True) 
        self.add_column('cijfer', dbc.TEXT)
        self.add_column('directory', dbc.TEXT)
        self.add_foreign_key('id', 'MILESTONES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

#NOTE: een index op FILES (bijvoorbeeld op filename, filetype of digest) ligt voor de hand
# Bij onderzoek blijkt echter dat dit bij de huidige grootte van de database (700 files) 
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
        self.add_column('aanvraag_id', dbc.INTEGER)
        # self.add_index('name_index', 'filename')
        # self.add_index('digest_index', 'digest')
        # self.add_index('name_digest_index', ['digest','name'])

        # de volgende Foreign Key ligt voor de hand. Er kunnen echter ook niet-aanvraag-gelinkte files zijn (File.Type.InvalidPDF) die om efficientieredenen toch worden opgeslagen
        # (dan worden ze niet steeds opnieuw ingelezen). De eenvoudigste remedie is om de foreign key te laten vervallen. 
        #
        # self.add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        #
        # TODO: Je zou nog kunnen overwegen een check te doen bij de aanmaak. Als er een INSERT of UPDATE is met een invalid aanvraag_id (trigger) kan je een exception raisen. 
        # Dit is wel ingewikkeld, want moet ook op de AANVRAGEN tabel (on DELETE) worden gechecked. Voorlopig werkt het zo waarschijnlijk ook wel.
        # Andere oplossing: een "lege" aanvraag opslaan en daarnaar verwijzen. Kan weer andere problemen veroorzaken, maar als het kan worden opgevangen in storage.py is het misschien 
        # toch de netste oplossing.
        #
        # Andere oplossing (netter): haal de aanvraag link naar een koppeltabel. Dan kan de koppeltable met een (tweetal) foreign keys 
        # werken en mogen files ook ongekoppeld blijven.
        
class ActionLogTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('ACTIONLOG')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('description', dbc.TEXT)
        self.add_column('action', dbc.INTEGER)    
        self.add_column('user', dbc.TEXT)    
        self.add_column('date', dbc.DATE)   
        self.add_column('can_undo', dbc.INTEGER)

class ActionLogAanvragenTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('ACTIONLOG_AANVRAGEN')
        self.add_column('log_id', dbc.INTEGER, primary = True)
        self.add_column('aanvraag_id', dbc.INTEGER, primary = True)  
        self.add_foreign_key('log_id', 'ACTIONLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('aanvraag_id', 'AANVRAGEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
       
class ActionLogFilesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('ACTIONLOG_FILES')
        self.add_column('log_id', dbc.INTEGER, primary = True)
        self.add_column('file_id', dbc.INTEGER, primary = True)    
        self.add_foreign_key('log_id', 'ACTIONLOG', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('file_id', 'FILES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
    
class BaseDirsTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BASEDIRS')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('year', dbc.INTEGER)
        self.add_column('period', dbc.TEXT)
        self.add_column('forms_version', dbc.TEXT)
        self.add_column('directory', dbc.TEXT)

class StudentMilestonesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENT_MILESTONES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('basedir_id', dbc.INTEGER)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('basedir_id', 'BASEDIRS', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class StudentMilestonesDetailsTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENT_MILESTONES_DETAILS')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('milestones_id', dbc.INTEGER)
        self.add_column('milestone_id', dbc.INTEGER)
        self.add_column('milestone_type', dbc.INTEGER)    
        self.add_foreign_key('milestones_id', 'STUDENT_MILESTONES', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

# ViewDefinition('VIEW_AANVRAGEN', column_names=['id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','datum_str'],
#                        select = SQLselect(MilestoneTableDefinition(), alias='M', joins=['AANVRAGEN as A'], where=SQE('M.ID', Ops.EQ, 'A.ID'),
#                     columns=['M.id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','datum_str']))

class AanvragenViewDefinition(ViewDefinition):
    def __init__(self):
        super().__init__('VIEW_AANVRAGEN', 
                         column_names=['id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','datum_str'],
                         key = 'id', select = SQLselect(MilestoneTableDefinition(), alias='M', joins=['AANVRAGEN as A'], where=SQE('M.ID', Ops.EQ, 'A.ID'),
                        columns=['M.id','datum','stud_id', 'bedrijf_id', 'titel','kans','status','beoordeling','datum_str']))                                 

class AAPSchema(Schema):
    ALL_TABLES:list[Type[TableDefinition]] = [
        VersionTableDefinition,
        FileRootTableDefinition,
        StudentTableDefinition,
        BedrijfTableDefinition,
        AanvraagTableDefinition,
        VerslagTableDefinition,
        FilesTableDefinition,
        ActionLogTableDefinition,
        ActionLogAanvragenTableDefinition,
        ActionLogFilesTableDefinition,
        BaseDirsTableDefinition,
        StudentMilestonesTableDefinition,
        StudentMilestonesDetailsTableDefinition,
        MilestoneTableDefinition,        
    ]
    ALL_VIEWS:list[Type[ViewDefinition]]= [ 
                AanvragenViewDefinition,
                ]
    def __init__(self):
        super().__init__()
        for tabledef in AAPSchema.ALL_TABLES:
            self.add_table(tabledef())
        for viewdef in AAPSchema.ALL_VIEWS:
            self.add_view(viewdef())

class AAPDatabase(Database):
    def __init__(self, filename, _reset_flag = False, ignore_version=False):
        super().__init__(filename, _reset_flag)
        self.schema = Schema.read_from_database(self)  
        if not self._reset_flag: 
            version_correct = self.check_version(recreate=False,ignore_error=ignore_version)
            if version_correct:
                self.load_roots(False)
                self.reset_keys()
    def reset_keys(self):
        def is_keyed_table(table: TableDefinition)->bool:
            return len(table.keys) == 1 and table.column(table.key).type==dbc.INTEGER and table.key == 'id' 
        # keyed_tables:list[TableDefinition] = [AanvraagTableDefinition(), VerslagTableDefinition(), ActionLogTableDefinition(), BedrijfTableDefinition(), FilesTableDefinition()]
        for table in self.schema.tables():            
            if is_keyed_table(table):
                reset_key(table.name, self.__find_max_key(table.name))
    def __find_max_key(self, table_name: str):
        if (row := self._execute_sql_command(f'select max(ID) from {table_name};', return_values = True)) and \
                                            (r0 := list(row[0])[0]):
            return r0 
        else:
            return 0
    @classmethod
    def create_from_schema(cls, schema: Schema, filename: str):
        result = super().create_from_schema(schema, filename)
        if result:
            result.check_version(recreate=True)
            result.load_roots(True)
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
    def load_roots(self, recreate = False):
        log_info('--- Laden paden voor File Encoding')
        if recreate:
            create_roots(self)
        else:
            load_roots(self)
        log_info(f'Bekende paden:\n{get_roots_report()}')
        log_info('--- Einde laden paden File Encoding')


        
