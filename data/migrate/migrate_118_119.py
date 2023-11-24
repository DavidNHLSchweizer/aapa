from data.aapa_database import AanvraagFilesTableDefinition, AanvraagTableDefinition, BaseDirsTableDefinition, FilesTableDefinition, StudentAanvragenTableDefinition, StudentMilestonesTableDefinition, StudentVerslagenTableDefinition, \
        StudentTableDefinition, VerslagFilesTableDefinition, VerslagTableDefinition, load_roots
from data.classes.base_dirs import BaseDir
from data.classes.files import File
from data.roots import encode_path
from data.storage.aapa_storage import AAPAStorage
from database.sql_table import SQLcreateTable
from database.database import Database
from database.table_def import ForeignKeyAction, TableDefinition
from general.log import log_debug
from general.name_utils import Names
import database.dbConst as dbc
from general.timeutil import TSC
# Wijzigingen in 1.19 voor migratie:
#
# studenten krijgt ook zijn eigen ID. Aanpassingen aan AANVRAGEN hiervoor
# voorbereiding: aanvraag_nr -> kans
# toevoegen verslagen tabel
# toevoegen basedirs tabel
# toevoegen student_milestones en student_milestones_details tabel
# creating VIEW_AANVRAGEN en VIEW_VERSLAGEN
#
def modify_studenten_table(database: Database):
    print('adding primary key to STUDENTEN table.')
    database._execute_sql_command('alter table STUDENTEN RENAME TO OLD_STUDENTEN')
    print('creating the new table')
    database.execute_sql_command(SQLcreateTable(StudentTableDefinition()))
    database._execute_sql_command('insert into STUDENTEN(stud_nr,full_name,first_name,email,tel_nr) select stud_nr,full_name,first_name,email,tel_nr from OLD_STUDENTEN', [])
    database._execute_sql_command('drop table OLD_STUDENTEN')
    print('end adding primary key to STUDENTEN table.')

def modify_aanvragen_table(database: Database):
    print('modifying AANVRAGEN table.')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    print('creating the new table')
    aanvragen_table = AanvraagTableDefinition() 
    database.execute_sql_command(SQLcreateTable(aanvragen_table))
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN(id,bedrijf_id,datum_str,titel,status,beoordeling,kans,versie)'+ \
                                  ' select id,bedrijf_id,datum_str,titel,status,beoordeling,aanvraag_nr,aanvraag_nr from OLD_AANVRAGEN', [])
    print('adding new STUDENT references to AANVRAGEN table.')
    sql = 'SELECT AANVRAGEN.id,STUDENTEN.id FROM AANVRAGEN,OLD_AANVRAGEN,STUDENTEN \
        WHERE ((STUDENTEN.stud_nr=OLD_AANVRAGEN.stud_nr) AND (AANVRAGEN.ID=OLD_AANVRAGEN.ID))'
    for row in database._execute_sql_command(sql, [], True):
        database._execute_sql_command('update AANVRAGEN set stud_id=? where id=?', [row[1], row[0]])
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    #kans en versie komt niet echt uit de verf, maar dat is lastig oplosbaar, laat eerst maar zo. 
    print('end modifying STUDENT references to AANVRAGEN table.')
    print('end modifying AANVRAGEN table.')

class OldFilesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('FILES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('filename', dbc.TEXT)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('digest', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        self.add_column('aanvraag_id', dbc.INTEGER)

def modify_files_table(database: Database):
    def transform_time_str(value: str)->str:
        return TSC.timestamp_to_sortable_str(TSC.str_to_timestamp(value))
    print('modifying FILES table.')
    database._execute_sql_command('alter table FILES RENAME TO OLD_FILES')
    # print('copying the timestamps to AANVRAGEN table.')
    # database._execute_sql_command(f'update aanvragen set datum = (SELECT timestamp from OLD_FILES WHERE AANVRAAG_ID=AANVRAGEN.ID)')
    print('creating the new FILES table')
    database.execute_sql_command(SQLcreateTable(FilesTableDefinition()))
    #copying the data except the timestamp
    database._execute_sql_command('insert into FILES(id,filename, digest,filetype)'+ \
                                  ' select id,filename, digest,filetype from OLD_FILES')
    #copying and transforming the timestamps
    for row in database._execute_sql_command('select id, timestamp, filetype, filename from OLD_FILES', [], True):
        database._execute_sql_command('update FILES set timestamp=? where id=?', [transform_time_str(row['timestamp']), row['id']]) 
    print('copying the timestamps to AANVRAGEN table.')

    database._execute_sql_command(f'update aanvragen set datum = (SELECT timestamp from OLD_FILES WHERE AANVRAAG_ID=AANVRAGEN.ID and filetype=?)',
                                  [File.Type.AANVRAAG_PDF])
    # transforming the timestamps
    for row in database._execute_sql_command('select id, datum from AANVRAGEN', [], True):
        database._execute_sql_command('update AANVRAGEN set datum=? where id=?', [transform_time_str(row['datum']), row['id']]) 
    
    print('creating new AANVRAGEN_FILES table')
    database.execute_sql_command(SQLcreateTable(AanvraagFilesTableDefinition()))
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN_FILES(aanvraag_id,file_id)'+ \
                                  ' select aanvraag_id,id from OLD_FILES where aanvraag_id != ?', [-1])
    database._execute_sql_command('drop table OLD_FILES')
    print('end creating AANVRAGEN_FILES table.')
    print('end modifying FILES table.')

# AanvragenFilesTableDefinition
def _init_base_directories(database: Database):
    known_bases = [
               BaseDir(2020, '1', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1'),
               BaseDir(2020, '1B', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B'),
               BaseDir(2020, '2', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2'),
               BaseDir(2021, '1', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1'),
               BaseDir(2021, '2', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2'),
               BaseDir(2021, '3', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3'),
               BaseDir(2021, '4', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4'),
               BaseDir(2022, '1', 'v3.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1'),
               BaseDir(2022, '2', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2'),
               BaseDir(2022, '3', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3'),
               BaseDir(2022, '4', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4'),
               BaseDir(2023, '1', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024') 
    ]
    storage = AAPAStorage(database)
    load_roots(database)
    for entry in known_bases:
        storage.add_file_root(entry.directory)
        database._execute_sql_command(
            "insert into BASEDIRS('year', 'period', 'forms_version', 'directory') values (?,?,?,?)", [entry.year, entry.period, entry.forms_version, encode_path(entry.directory)])        

# toevoegen VERSLAGEN tabel en BASEDIRS tabel
# toevoegen STUDENT_MILESTONES en STUDENT_MILESTONES_DETAILS tabel
def create_verslagen_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN en VERSLAG_FILES')
    database.execute_sql_command(SQLcreateTable(VerslagTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagFilesTableDefinition()))
    print('toevoegen nieuwe tabel BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    print('initialiseren waardes voor BASEDIRS')
    _init_base_directories(database)
    print('toevoegen nieuwe STUDENT_MILESTONES, STUDENT_AANVRAGEN en STUDENT_VERSLAGEN tabellen')
    database.execute_sql_command(SQLcreateTable(StudentMilestonesTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(StudentAanvragenTableDefinition())) 
    database.execute_sql_command(SQLcreateTable(StudentVerslagenTableDefinition())) 
    print('--- klaar toevoegen nieuwe tabellen')

#aanpassen voornamen waar nodig
def correct_first_names(database: Database):
    print('correcting incorrect first names in STUDENTEN')
    for row in database._execute_sql_command('select id,full_name,first_name from STUDENTEN', [], True):
        parsed = Names.parsed(row['full_name'])
        if parsed.first_name != row['first_name']:
            print(f'\tCorrecting {row["full_name"]}')
            database._execute_sql_command('update STUDENTEN set first_name=? where id=?', [parsed.first_name, row['id']])
    print('--- ready incorrect first names in STUDENTEN')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        modify_studenten_table(database)
        modify_aanvragen_table(database)    
        modify_files_table(database)
        create_verslagen_tables(database)
        correct_first_names(database)
