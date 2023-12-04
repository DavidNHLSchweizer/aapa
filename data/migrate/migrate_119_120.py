from data.aapa_database import BaseDirsTableDefinition, StudentAanvragenTableDefinition, StudentMilestonesTableDefinition, StudentVerslagenTableDefinition, VerslagFilesTableDefinition, VerslagTableDefinition, load_roots
from data.classes.base_dirs import BaseDir
from data.migrate.migrate_118_119 import _init_base_directories
from data.storage.aapa_storage import AAPAStorage
from database.database import Database
from database.sql_table import SQLcreateTable

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

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        create_verslagen_tables(database)
        _init_base_directories(database)
