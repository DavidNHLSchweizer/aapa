from __future__ import annotations
import datetime
from enum import IntEnum
from textwrap import TextWrapper
from typing import TextIO
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.general.class_codes import ClassCodes
from data.general.const import FileType, MijlpaalBeoordeling, MijlpaalType
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from database.classes.sql_table import SQLcreateTable, SQLselect
from database.classes.sql_view import SQLcreateView
from database.classes.table_def import ForeignKeyAction, TableDefinition
from database.classes.database import Database, Schema
import database.classes.dbConst as dbc
from database.classes.view_def import ViewDefinition
from general.keys import reset_key
from main.config import config
from main.log import log_error, log_info, log_warning
from main.versie import Versie
from data.general.roots import Roots

class AAPaException(Exception): pass

DBVERSION = '1.24'
class DBVersie(Versie):
    def __init__(self, db_versie = DBVERSION, **kwargs):
        super().__init__(**kwargs)
        self.db_versie = db_versie
    def __str__(self)->str:
        return self.db_versie

class VersionTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('VERSIE', autoid=True)
        self.add_column('db_versie', dbc.TEXT)
        self.add_column('versie', dbc.TEXT)
        self.add_column('datum', dbc.TEXT)

def read_version_info(database: Database)->DBVersie:
    if row := database._execute_sql_command('select db_versie,versie,datum from VERSIE order by id desc limit 1', [], True):
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
    for code,root in Roots.get_roots():
        create_root(database, code, root)        
            
def load_roots(database: Database):
    Roots.reset_roots()
    for row in database._execute_sql_command('select code, root from fileroot', [], True): 
        if row['code'] == ':ROOT1:':
            continue # first row is already loaded, this is the NHL Stenden BASEPATH
        Roots.add_root(Roots.decode_path(row['root']), row['code']) 
            
class DetailTableDefinition2(TableDefinition):
    def __init__(self, name: str, 
                 main_table_name: str, main_alias_id: str):
        super().__init__(name)
        self._detail_tables = {}
        self.add_column(main_alias_id, dbc.INTEGER, primary = True)
        self.add_column('detail_id', dbc.INTEGER, primary = True)          
        self.add_column('class_code', dbc.TEXT, primary = True)  
        self.add_foreign_key(main_alias_id, main_table_name, 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        #NOTE: no foreign key on second column, this could be coupled to more than one table
        #   class_code determines how to interpret detail_id!
    def add_detail(self, detail_code: str, detail_table: TableDefinition):
        self._detail_tables[detail_code] = detail_table

class StudentTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('STUDENTEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_nr', dbc.TEXT)
        self.add_column('full_name', dbc.TEXT)
        self.add_column('first_name', dbc.TEXT)
        self.add_column('email', dbc.TEXT, notnull=True)
        self.add_column('status', dbc.INTEGER)

class BedrijfTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BEDRIJVEN')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('name', dbc.TEXT)    

class MijlpaalTableDefinition(TableDefinition):
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

class AanvraagTableDefinition(MijlpaalTableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('versie', dbc.INTEGER)

class AanvraagDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('AANVRAGEN_DETAILS', main_table_name='AANVRAGEN', main_alias_id='aanvraag_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

class VerslagTableDefinition(MijlpaalTableDefinition):
    def __init__(self):
        super().__init__('VERSLAGEN')
        self.add_column('verslag_type', dbc.INTEGER)
        self.add_column('cijfer', dbc.TEXT)

class VerslagenDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('VERSLAGEN_DETAILS', main_table_name='VERSLAGEN', main_alias_id='verslag_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

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
        self.add_column('mijlpaal_type', dbc.INTEGER)
        self.add_index('name_index', 'filename')
        # self.add_index('digest_index', 'digest')
        # self.add_index('name_digest_index', ['digest','name'])

class UndoLogTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('UNDOLOGS')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('description', dbc.TEXT)
        self.add_column('action', dbc.INTEGER)    
        self.add_column('processing_mode', dbc.INTEGER)    
        self.add_column('user', dbc.TEXT)    
        self.add_column('date', dbc.DATE)   
        self.add_column('can_undo', dbc.INTEGER)

class UndologsDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('UNDOLOGS_DETAILS', main_table_name='UNDOLOGS', main_alias_id='log_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(Aanvraag), detail_table=AanvraagTableDefinition)
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)
        self.add_detail(detail_code=ClassCodes.classtype_to_code(Verslag), detail_table=VerslagTableDefinition)
    
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
        super().__init__('STUDENT_DIRECTORIES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('directory', dbc.TEXT)
        self.add_column('basedir_id', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('basedir_id', 'BASEDIRS', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

class StudentDirectoriesDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('STUDENT_DIRECTORIES_DETAILS', main_table_name='STUDENT_DIRECTORIES', main_alias_id='stud_dir_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(MijlpaalDirectory), detail_table=MijlpaalDirectoryTableDefinition)

class MijlpaalDirectoryTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('MIJLPAAL_DIRECTORIES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('mijlpaal_type', dbc.INTEGER)
        self.add_column('kans', dbc.INTEGER)
        self.add_column('directory', dbc.TEXT)
        self.add_column('datum', dbc.TEXT)

class MijlpaalDirectoriesDetailsTableDefinition(DetailTableDefinition2):
    def __init__(self):
        super().__init__('MIJLPAAL_DIRECTORIES_DETAILS', main_table_name='MIJLPAAL_DIRECTORIES', main_alias_id='mp_dir_id')
        self.add_detail(detail_code=ClassCodes.classtype_to_code(File), detail_table=FilesTableDefinition)

#-------------------- views -------------------------------
def get_sql_cases_for_int_type(column_name: str, int_class: IntEnum, alias_name: str)->str:
    all_cases = " ".join([f'when {int(elem)} then "{str(elem)}"' for elem in int_class])
    return f'(case {column_name} {all_cases} else "?" end ) as {alias_name}'

def get_int_type_for_sql_cases(column_name: str, int_class: IntEnum)->str:
    reverse_dict= {str(elem):int(elem) for elem in int_class}
    all_cases = " ".join([f'when "{str(elem)}" then {reverse_dict[str(elem)]}' for elem in int_class])
    return f'(case {column_name} {all_cases} else "?" end )'

class AanvragenOverzichtDefinition(ViewDefinition):
    def __init__(self):
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        bedrijf = '(select name from BEDRIJVEN as B where B.ID = A.bedrijf_id) as bedrijf'
        beoordeling = get_sql_cases_for_int_type('beoordeling', MijlpaalBeoordeling, 'beoordeling')
        super().__init__('AANVRAGEN_OVERZICHT', 
                         query=f'select id,{stud_name},datum,{bedrijf},titel,versie,kans,{beoordeling} from AANVRAGEN as A order by 2,3')
        
class StudentDirectoriesOverzichtDefinition(ViewDefinition):
    def __init__(self):
        stud_status_str = get_sql_cases_for_int_type('s.status', Student.Status, 'student_status') 
        query = f'select s.id,full_name,stud_nr,{stud_status_str},bd.year,bd.period,sdd.directory as "(laatste) directory" from studenten as s \
inner join student_directories as sdd on s.id = sdd.stud_id \
inner join basedirs as bd on sdd.basedir_id = bd.id \
group by sdd.stud_id having max(sdd.id) order by 5,6,2'
        super().__init__('STUDENT_DIRECTORIES_OVERZICHT', query=query)

class AanvragenFileOverzichtDefinition(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        stud_name = '(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student'
        innerjoins = 'inner join AANVRAGEN_DETAILS as AD on A.ID=AD.aanvraag_id inner join FILES as F on F.ID=AD.detail_id'
        super().__init__('AANVRAGEN_FILE_OVERZICHT', 
                         query=f'select A.id as aanvraag_id,{stud_name},titel, F.ID as file_id,F.filename as filename,{filetype_str} \
                                from AANVRAGEN as A {innerjoins} where AD.class_code="{ClassCodes.classtype_to_code(File)}" order by 2')

class StudentDirectoriesFileOverzichtDefinition(ViewDefinition):
    def __init__(self):
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType, 'filetype') 
        mijlpaal_str = get_sql_cases_for_int_type('F.mijlpaal_type', MijlpaalType, 'mijlpaal') 
        status_str = get_sql_cases_for_int_type('sd.status', StudentDirectory.Status, 'dir_status') 
        query = \
f'select SD.id,SD.STUD_ID,SD.directory as student_directory,{status_str},MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,{filetype_str},{mijlpaal_str} \
from STUDENT_DIRECTORIES as SD \
inner join STUDENT_DIRECTORIES_DETAILS as SDD on SD.id=SDD.stud_dir_id \
inner join MIJLPAAL_DIRECTORIES as MD on MD.id=SDD.detail_id \
inner join MIJLPAAL_DIRECTORIES_DETAILS as MDF on MD.ID=MDF.mp_dir_id \
inner join FILES as F on F.ID=MDF.detail_id'
        super().__init__('STUDENT_DIRECTORIES_FILE_OVERZICHT', query=query)

class StudentMijlpaalDirectoriesOverzichtDefinition(ViewDefinition):
    def __init__(self):
        mijlpaal_str = get_sql_cases_for_int_type('MPD.mijlpaal_type', MijlpaalType, 'mijlpaal_type') 
        query = f'select (select full_name from studenten as S where S.id=SD.stud_id) as student, MPD.datum, {mijlpaal_str}, MPD.kans, MPD.directory \
                from student_directories as SD \
                inner join STUDENT_DIRECTORIES_DETAILS as SDD on SD.ID=SDD.stud_dir_id \
                inner join MIJLPAAL_DIRECTORIES as MPD on MPD.ID=SDD.detail_id order by 1,3'
        super().__init__('STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT', query=query)

class StudentVerslagenOverzichtDefinition(ViewDefinition):
    #TODO: toevoegen filename en/of datum. Wat lastiger dan gedacht, voorlopig maar even weggelaten
    def __init__(self):
        verslag_type_str = get_sql_cases_for_int_type('V.verslag_type', MijlpaalType, 'verslag_type') 
        status_str = get_sql_cases_for_int_type('V.status', Verslag.Status, 'status') 
        beoordeling = get_sql_cases_for_int_type('V.beoordeling', MijlpaalBeoordeling, 'beoordeling')
        filetype_str = get_sql_cases_for_int_type('F.filetype', FileType,'filetype')
        query = f'select V.id as verslag_id, V.stud_id, (select full_name from STUDENTEN as S where S.id=V.stud_id) as student, V.datum, {verslag_type_str}, \
            (select name from BEDRIJVEN as B where B.id=V.bedrijf_id) as bedrijf, V.titel,V.kans, F.id as file_id, F.filename,{filetype_str},{status_str},{beoordeling} \
            from VERSLAGEN as V inner join VERSLAGEN_DETAILS as VD on VD.verslag_id = V.id inner join FILES as F on F.ID=VD.detail_id order by 3,4'        
        super().__init__('STUDENT_VERSLAGEN_OVERZICHT', query=query)

class AAPaSchema(Schema):
    ALL_TABLES:list[TableDefinition] = [
        VersionTableDefinition,
        FileRootTableDefinition,
        StudentTableDefinition,
        BedrijfTableDefinition,
        AanvraagTableDefinition,
        AanvraagDetailsTableDefinition,
        FilesTableDefinition,
        UndoLogTableDefinition,
        UndologsDetailsTableDefinition,
        VerslagTableDefinition,
        VerslagenDetailsTableDefinition,
        BaseDirsTableDefinition,
        StudentDirectoryTableDefinition,    
        StudentDirectoriesDetailsTableDefinition, 
        MijlpaalDirectoryTableDefinition, 
        MijlpaalDirectoriesDetailsTableDefinition,        
    ]
    ALL_VIEWS:list[ViewDefinition]= [ 
                AanvragenOverzichtDefinition,
                StudentDirectoriesOverzichtDefinition,
                AanvragenFileOverzichtDefinition,
                StudentDirectoriesFileOverzichtDefinition,
                StudentMijlpaalDirectoriesOverzichtDefinition,
                ]
    def __init__(self):
        super().__init__()
        for tabledef in self.ALL_TABLES:
            self.add_table(tabledef())
        for viewdef in self.ALL_VIEWS:
            self.add_view(viewdef())
    @staticmethod
    def _dump_view_or_table_sql(table_or_view: TableDefinition|ViewDefinition, file:TextIO, wrapper: TextWrapper=None):
        if isinstance(table_or_view, TableDefinition):
            file.write(f'table {table_or_view.name}:\n')
            sql = SQLcreateTable(table_or_view)
        else:
            file.write(f'view {table_or_view.name}:\n')
            sql = SQLcreateView(table_or_view)
        if not wrapper: 
            wrapper = TextWrapper(initial_indent="  ", subsequent_indent="  ")
        for line in wrapper.wrap(sql.query):
            file.write(f'{line}\n')
    @staticmethod
    def dump_schema_sql(filename: str):
        wrapper = TextWrapper(width=120, initial_indent="  ", subsequent_indent="  ",
                              break_long_words=False)
        with open(filename, mode="w", encoding='utf-8') as file:
            timestr = datetime.datetime.strftime(datetime.datetime.now(), f'%d-%m-%Y %H:%M:%S')
            file.write(f'AAPA Database schema versie {DBVERSION}\n{timestr}\n\n')
            for table in AAPaSchema.ALL_TABLES:
                AAPaSchema._dump_view_or_table_sql(table(),file, wrapper)  
            file.write(f'\n')
            for view in AAPaSchema.ALL_VIEWS:
                AAPaSchema._dump_view_or_table_sql(view(),file, wrapper)   

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
    def load_file_roots(self, recreate = False, verbose=False):
        log_info('--- Laden paden voor File Encoding')
        if recreate:
            create_roots(self)
        else:
            load_roots(self)
        if verbose:
            report = '\n'.join([f'{code} = "{root}"' for (code,root) in Roots.get_roots()])
            log_info(f'Bekende paden:\n{report}')
            log_info('--- Einde laden paden File Encoding')


        
