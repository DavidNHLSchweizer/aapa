# drop view if exists test_aanvragen;
# create view if not exists test_aanvragen as select M.id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,datum_str from MILESTONES M,NEW_AANVRAGEN A where M.ID = A.id and milestone_type=1 

from enum import IntEnum

from pathlib import Path
from data.AAPdatabase import AanvragenViewDefinition, BaseDirsTableDefinition, MilestoneTableDefinition, AanvraagTableDefinition, StudentMilestonesDetailsTableDefinition, StudentMilestonesTableDefinition, StudentTableDefinition, VerslagTableDefinition, load_roots
from data.classes.base_dirs import BaseDir
from data.classes.milestones import Milestone
from data.roots import encode_path
from data.storage import AAPAStorage
from database.SQL import SQLcreate, SQLinsert, SQLselect
from database.database import Database
from database.sqlexpr import SQE, Ops
from database.tabledef import ForeignKeyAction, TableDefinition
from database.viewdef import SQLcreateView, ViewDefinition
from general.name_utils import Names
import database.dbConst as dbc
# Wijzigingen in 1.19 voor migratie:
#
# studenten krijgt ook zijn eigen ID. Aanpassingen aan AANVRAGEN hiervoor
# voorbereiding: aanvraag_nr -> kans
# toevoegen verslagen tabel
# toevoegen basedirs tabel
# toevoegen student_milestones en student_milestones_details tabel
#
def modify_studenten_table(database: Database):
    print('adding primary key to STUDENTEN table.')
    database._execute_sql_command('alter table STUDENTEN RENAME TO OLD_STUDENTEN')
    print('creating the new table')
    database.execute_sql_command(SQLcreate(StudentTableDefinition()))
    database._execute_sql_command('insert into STUDENTEN(stud_nr,full_name,first_name,email,tel_nr) select stud_nr,full_name,first_name,email,tel_nr from OLD_STUDENTEN', [])
    database._execute_sql_command('drop table OLD_STUDENTEN')
    print('end adding primary key to STUDENTEN table.')


class OldAanvraagTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('AANVRAGEN')
        self.add_column('id', dbc.INTEGER, primary = True) 
        self.add_column('stud_id', dbc.INTEGER)
        self.add_column('bedrijf_id', dbc.INTEGER)
        self.add_column('datum_str', dbc.TEXT)
        self.add_column('titel', dbc.TEXT)
        self.add_column('kans', dbc.INTEGER)
        self.add_column('status', dbc.INTEGER)
        self.add_column('beoordeling', dbc.INTEGER)
        self.add_foreign_key('stud_id', 'STUDENTEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)
        self.add_foreign_key('bedrijf_id', 'BEDRIJVEN', 'id', onupdate=ForeignKeyAction.CASCADE, ondelete=ForeignKeyAction.CASCADE)

def modify_aanvragen_table(database: Database):
    print('modifying AANVRAGEN table.')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    print('creating the new table')
    aanvragen_table = OldAanvraagTableDefinition() 
    database.execute_sql_command(SQLcreate(aanvragen_table))
    #copying the data
    database._execute_sql_command('insert into AANVRAGEN(id,bedrijf_id,datum_str,titel,kans,status,beoordeling)'+ \
                                  ' select id,bedrijf_id,datum_str,titel,aanvraag_nr,status,beoordeling from OLD_AANVRAGEN', [])
    print('adding new STUDENT references to AANVRAGEN table.')
    sql = 'SELECT AANVRAGEN.id,STUDENTEN.id FROM AANVRAGEN,OLD_AANVRAGEN,STUDENTEN \
        WHERE ((STUDENTEN.stud_nr=OLD_AANVRAGEN.stud_nr) AND (AANVRAGEN.ID=OLD_AANVRAGEN.ID))'
    for row in database._execute_sql_command(sql, [], True):
        database._execute_sql_command('update AANVRAGEN set stud_id=? where id=?', [row[1], row[0]])
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    print('end modifying STUDENT references to AANVRAGEN table.')
    print('end modifying AANVRAGEN table.')

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
def create_new_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN')
    database.execute_sql_command(SQLcreate(VerslagTableDefinition()))
    print('toevoegen nieuwe tabel BASEDIRS')
    database.execute_sql_command(SQLcreate(BaseDirsTableDefinition()))
    print('initialiseren waardes voor BASEDIRS')
    _init_base_directories(database)
    print('toevoegen nieuwe tabel STUDENT_MILESTONES')
    database.execute_sql_command(SQLcreate(StudentMilestonesTableDefinition())) 
    print('toevoegen nieuwe tabel STUDENT_MILESTONE_DETAILS')
    database.execute_sql_command(SQLcreate(StudentMilestonesDetailsTableDefinition())) 
    print('--- klaar toevoegen nieuwe tabellen')

def create_milestones_table(database: Database):
    print('toevoegen nieuwe tabel MILESTONES en aanpassen AANVRAGEN')
    database.execute_sql_command(SQLcreate(MilestoneTableDefinition()))
    print('kopieren data in AANVRAGEN naar MILESTONES')
    sql = "select id,stud_id,bedrijf_id,titel,kans,status,beoordeling from AANVRAGEN"
    sql2 = "insert into MILESTONES(id,milestone_type,stud_id,bedrijf_id,titel,kans,beoordeling,status) values(?,?,?,?,?,?,?,?)"
    for row in database._execute_sql_command(sql, [], True):
        beoord = str(Milestone.Beoordeling(row['beoordeling']))
        database._execute_sql_command(sql2,[row['id'],int(Milestone.Type.AANVRAAG),
                                            row['stud_id'],row['bedrijf_id'],
                                            row['titel'],row['kans'],beoord,row['status']])
    # database.commit()
    database._execute_sql_command('UPDATE MILESTONES SET datum=\
                (select timestamp from FILES WHERE FILES.aanvraag_id=MILESTONES.ID and filetype=0)',
            [])            
    print('aanpassen tabel AANVRAGEN')
    database._execute_sql_command('alter table AANVRAGEN RENAME TO OLD_AANVRAGEN')
    database.execute_sql_command(SQLcreate(AanvraagTableDefinition()))
    sql = "insert into AANVRAGEN(id,datum_str) select id,datum_str FROM OLD_AANVRAGEN"
    database._execute_sql_command(sql, [])
    database._execute_sql_command('drop table OLD_AANVRAGEN')
    print('--- klaar toevoegen nieuwe tabel MILESTONES en aanpassen AANVRAGEN')

#aanpassen voornamen waar nodig
def correct_first_names(database: Database):
    print('correcting incorrect first names in STUDENTEN')
    for row in database._execute_sql_command('select id,full_name,first_name from STUDENTEN', [], True):
        parsed = Names.parsed(row['full_name'])
        if parsed.first_name != row['first_name']:
            print(f'\tCorrecting {row["full_name"]}')
            database._execute_sql_command('update STUDENTEN set first_name=? where id=?', [parsed.first_name, row['id']])
    print('--- ready incorrect first names in STUDENTEN')

#create VW_AANVRAGEN view:
def create_view(database: Database):
    print('--- creating view VIEW_AANVRAGEN ...')
    database.execute_sql_command(SQLcreateView(AanvragenViewDefinition()))
    print('--- klaar creating view VIEW_AANVRAGEN')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        modify_studenten_table(database)
        modify_aanvragen_table(database)    
        create_new_tables(database)
        correct_first_names(database)
        create_milestones_table(database)
        create_view(database)
