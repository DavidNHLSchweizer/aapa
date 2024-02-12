import datetime
import re
from typing import Tuple
from database.aapa_database import BaseDirsTableDefinition, MijlpaalDirectory_FilesTableDefinition, MijlpaalDirectoryTableDefinition, StudentDirectoriesFileOverzichtDefinition, StudentDirectoriesOverzichtDefinition, StudentDirectory_DirectoriesTableDefinition, \
        StudentDirectoryTableDefinition, VerslagFilesTableDefinition, VerslagTableDefinition, \
        create_roots
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from migrate.m119.old_roots import old_add_root, old_decode_path, old_reset_roots
from general.sql_coll import SQLcollectors
from data.general.roots import OneDriveCoder, add_root, encode_path, get_onedrive_root, reset_roots
from storage.aapa_storage import AAPAStorage
from database.classes.database import Database
from database.classes.sql_table import SQLcreateTable
from database.classes.sql_view import SQLcreateView
from database.classes.table_def import TableDefinition
import database.classes.dbConst as dbc
from general.keys import reset_key
from general.timeutil import TSC

# recoding all fileroots 
# toevoegen VERSLAGEN tabel en BASEDIRS tabel
# filling BASEDIRS with initial values
# toevoegen STUDENT_DIRECTORIES
#   en gerelateerde tabellen
# adding all known students with the correct status
# correction of errors in STUDENTEN tabel

class BackupFileRootTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BACKUP_FILEROOT', autoid=True)
        self.add_column('code', dbc.TEXT, unique=True)
        self.add_column('root', dbc.TEXT)

class BackupFilesTableDefinition(TableDefinition):
    def __init__(self):
        super().__init__('BACKUP_FILES')
        self.add_column('id', dbc.INTEGER, primary = True)
        self.add_column('filename', dbc.TEXT)
        self.add_column('timestamp', dbc.TEXT)
        self.add_column('digest', dbc.TEXT)
        self.add_column('filetype', dbc.INTEGER)
        self.add_column('mijlpaal_type', dbc.INTEGER)

def backup_tables(database: Database):
    database.execute_sql_command(SQLcreateTable(BackupFileRootTableDefinition()))
    database._execute_sql_command('insert into BACKUP_FILEROOT SELECT * from FILEROOT')
    database.execute_sql_command(SQLcreateTable(BackupFilesTableDefinition()))
    database._execute_sql_command('insert into BACKUP_FILES SELECT * from FILES')

def cleanup_backup(database: Database):
    database._execute_sql_command('drop table BACKUP_FILEROOT')
    database._execute_sql_command('drop table BACKUP_FILES')

def _update_roots_table(database:Database):        
    database._execute_sql_command('DELETE from FILEROOT')
    create_roots(database)

def create_mijlpalen_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN en VERSLAG_FILES')
    database.execute_sql_command(SQLcreateTable(VerslagTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagFilesTableDefinition()))
    print('toevoegen nieuwe STUDENT_DIRECTORY en gerelateerde tabellen')
    database.execute_sql_command(SQLcreateTable(StudentDirectoryTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(StudentDirectory_DirectoriesTableDefinition())) 
    database.execute_sql_command(SQLcreateTable(MijlpaalDirectoryTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(MijlpaalDirectory_FilesTableDefinition()))        

    print('--- klaar toevoegen nieuwe tabellen')

def init_base_directories(database: Database):
    known_bases = [
               BaseDir(2020, '1', 'v2.2b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1'),
               BaseDir(2020, '1B', 'v2.2b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B'),
               BaseDir(2020, '2', 'v2.2b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2'),
               BaseDir(2021, '1', 'v2.3b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1'),
               BaseDir(2021, '2', 'v2.3b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2'),
               BaseDir(2021, '3', 'v2.3b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3'),
               BaseDir(2021, '4', 'v2.3b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4'),
               BaseDir(2022, '1', 'v3.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1'),
               BaseDir(2022, '2', 'v4.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2'),
               BaseDir(2022, '3', 'v4.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3'),
               BaseDir(2022, '4', 'v4.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4'),
               BaseDir(2023, '1', 'v4.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Oud'),
               BaseDir(2023, '2', 'v5.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw'), 
    ]
    print('adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    print('initialisation values BASEDIRS')  
    for entry in known_bases:
        coded_path=add_root(fr'{OneDriveCoder.ONEDRIVE}\{entry.directory}')
        database._execute_sql_command(
            "insert into BASEDIRS('year', 'period', 'forms_version', 'directory') values (?,?,?,?)", 
            [entry.year, entry.period, entry.forms_version, coded_path])        
    print('--- ready adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    _update_roots_table(database)

def _start_with_new_roots(database: Database):
    known_roots = [rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Beoordeling aanvragen 2023',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Oud',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Oud\Beoordeling aanvragen 2023',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw',
                  ]
    database._execute_sql_command('DELETE from FILEROOT')
    reset_roots()  
    onedrive_root = get_onedrive_root()
    for root in known_roots:
        add_root(rf'{onedrive_root}\{root}')

def _find_old_roots(database: Database)->list[Tuple[str,str]]:
    result = []
    old_reset_roots()
    reset_key('ROOT')
    for row in database._execute_sql_command(f'select code,root from BACKUP_FILEROOT', return_values=True):
        root = old_decode_path(row['root'])
        old_add_root(root)
        result.append((row['code'], root))  
    return result

def _find_unused_roots(database: Database)->list[str]:
    sql = 'SELECT b1.code FROM backup_fileroot AS b1 WHERE (NOT EXISTS (SELECT filename FROM backup_files WHERE instr(filename,b1.code) > 0)) AND (NOT EXISTS (SELECT b2.root FROM backup_fileroot AS b2 WHERE instr(b2.root,b1.code) > 0))'
    return [row['code'] for row in database._execute_sql_command(sql, return_values=True)]

def _find_old_files(database: Database)->list[Tuple[int,str]]:
    result = [(row['id'], old_decode_path(row['filename'])) for 
               row in database._execute_sql_command(f'select id,filename from BACKUP_FILES', return_values=True)]
    # with open('OLD_FILES.txt', 'w', encoding='utf-8') as file:
    #     file.writelines(f'{str(f)}\n' for f in result)
    return result

def _find_all_files(database:Database):
    storage = AAPAStorage(database)
    result= [(file.id, file.filename) for file in storage.find_all('files')]
    # with open('NEW_FILES.txt', 'w', encoding='utf-8') as file:
    #     file.writelines(f'{str(f)}\n' for f in result)
    return result

def _check_results(old_files, new_files):    
    print('checking results...')
    warnings = 0
    for old_file,new_file in zip(old_files, new_files):
        old_id,old_name = old_file
        new_id,new_name = new_file
        if old_id != new_id:
            warning = 'ID!'
        else:
            warning = ""
        if old_name != new_name:
            warning = warning + '!DIFF!'
        if warning:
            print(f'{old_id}->{new_id}: {old_name}->{new_name} {warning}')
            warnings+=1
    if warnings == 0:
        print('OK!. No differences detected.')

def recode_roots_table(database: Database):
    print('re-coding (and probably simplifying) FILEROOT table')
    old_roots = _find_old_roots(database)
    old_files = _find_old_files(database)
    print('define new roots and recode existing roots')
    _start_with_new_roots(database)
    unused_roots = _find_unused_roots(database)
    # first code can be dropped, never used. 
    # second code is NHL Stenden onedrive root, already added 
    # so start at 2
    for code,root in old_roots[2:]: 
        if code in unused_roots:
            print(f'\tdropping unused code {code}')
            continue
        add_root(root)
    _update_roots_table(database)
    print('update FILES table')
    for id,filename in old_files:  
        database._execute_sql_command("update FILES set filename=? where id = ?", 
                                      [encode_path(filename), id])
    database.commit()
    _check_results(old_files, _find_all_files(database))

def modify_studenten_table(database: Database):
    print('initializing status column in STUDENTEN')
    #initialise status where aanvraag is "voldoende"
    select2 = 'select s.id from studenten as s where exists (select a.id from aanvragen as a where a.stud_id = s.id and a.beoordeling=2)'
    database._execute_sql_command(f'update STUDENTEN set STATUS=? where id in ({select2})', [Student.Status.BEZIG])
    database._execute_sql_command(f'update STUDENTEN set STATUS=? where status != ?', [Student.Status.AANVRAAG, Student.Status.BEZIG])
    database._execute_sql_command(f'update STUDENTEN set STATUS=? where status is null', [Student.Status.UNKNOWN])
    print('--- klaar initializing status column in STUDENTEN')

def correct_student_errors(database: Database, phase_1 = True):
    if phase_1:
        print('correcting some existing errors in STUDENTEN table (phase: 1)')  
    
        #jorunn Oosterwegel, jelke nelisse, Musaab Asawi
        database._execute_sql_command(f'update STUDENTEN set STATUS=? where id in (?,?,?)', 
                                    [Student.Status.AANVRAAG, 52,56,70])
        
        #Justin vd Leij
        database._execute_sql_command('update AANVRAGEN set stud_id = ? where stud_id = ?',
                                    [16,17]
                                    )
        database._execute_sql_command('delete from STUDENTEN where id = ?', [17])
        database._execute_sql_command(f'update STUDENTEN set STATUS=? where id = ?', 
                                    [Student.Status.BEZIG, 16])

        #Dennis Stiekema
        database._execute_sql_command('update STUDENTEN set stud_nr = ? where stud_nr = ?',
                                    ['3319902','319902']
                                    )
        #Jorn Postma
        database._execute_sql_command('update STUDENTEN set stud_nr = ? where stud_nr = ?',
                                    ['4672933','S4672933']
                                    )
        #Julian van Veen
        database._execute_sql_command('update STUDENTEN set stud_nr = ? where stud_nr = ?',
                                    ['4692519','S4692519']
                                    )
        #Peter van Schagen
        database._execute_sql_command('update STUDENTEN set stud_nr = ? where stud_nr = ?',
                                    ['3519642','519642']
                                    )
        #Georgina/Georgie Laskewitz
        database._execute_sql_command('update STUDENTEN set full_name = ?,first_name=?,email=? where stud_nr = ?',
                                    ['Georgie Laskewitz', 'Georgie','georgina.laskewitz@student.nhlstenden.com', '3556882']
                                    )
        


    if not phase_1:
        print('--- continuing correcting errors in STUDENTEN table')

        #Jimi/Cassandra van Oosten
        database._execute_sql_command(f'update aanvragen set stud_id = (select id from studenten where full_name=?) where stud_id=?',
                                      ["Cassandra van Oosten", 32])
        database._execute_sql_command(f'delete from STUDENTEN where id = ?', [32])

        # redmar eef sprenger ->redmar sprenger (ivm directories)
        database._execute_sql_command(f'update studenten set full_name = ? where stud_nr=?',
                                      ["Redmar Sprenger", "4670183"])

        print('--- klaar correcting errors in STUDENTEN table')


def _correct_date(date_fld: str)->str:
    PATTERN  = r'Datum (?P<date>.*)'
    if match := re.match(PATTERN, date_fld):
        date = datetime.datetime.strptime(match.group('date'), '%m/%d/%Y %I:%M:%S %p')
        return TSC.timestamp_to_sortable_str(date)
    return date_fld

def correct_aanvragen_errors(database: Database):
    print('--- correcting data in AANVRAGEN table')
    # Datum 12/16/2023 11:23:46 AM -> 2023-12-16 11:23:46        
    rows = database._execute_sql_command(f'select id,datum_str from aanvragen where datum_str like ?',
                                    [ "Datum %/%/____ %:%:% _M"], True)
    for row in rows:
        database._execute_sql_command(f'update aanvragen set datum_str = ? where id = ?',
                                        [_correct_date(row["datum_str"]), row["id"]])
    print('--- klaar correcting data in AANVRAGEN table')
        
def _import_json(database: Database, json_name: str):
    sqlcolls = SQLcollectors.read_from_dump(json_name)
    sqlcolls.execute_sql(database)

def import_studenten(database: Database, json_name: str):
    print("importing new students from generated list SQL-commandos")
    _import_json(database, json_name)
    print('--- klaar importeren nieuwe studenten')

def import_student_directories(database: Database):
    JSONS = ['2020-2021_Semester 1.json',
            '2020-2021_Semester 1B.json',
            '2020-2021_Semester 2.json',
            '2021-2022_Periode 1.json',
            '2021-2022_Periode 2.json',
            '2021-2022_Periode 3.json',
            '2021-2022_Periode 4.json',
            '2022-2023_Periode 1.json',
            '2022-2023_Periode 2.json',
            '2022-2023_Periode 3.json',
            '2022-2023_Periode 4.json',
            'HBO-ICT Afstuderen - Software Engineering_2023-2024 Oud.json',
            'HBO-ICT Afstuderen - Software Engineering_2023-2024 Nieuw.json',
            ]
    print("importing student directories from generated list SQL-commandos")
    for json_name in JSONS:
        _import_json(database, rf'.\migrate\m119\{json_name}')
    print("... ready importing student directories from generated list SQL-commandos")

def create_views(database: Database):
    print('creating views')
    print('student directories overzicht')
    database.execute_sql_command(SQLcreateView(StudentDirectoriesFileOverzichtDefinition()))
    database.execute_sql_command(SQLcreateView(StudentDirectoriesOverzichtDefinition()))
    print('--- ready creating views')

def migrate_database(database: Database, phase = 42):    
    with database.pause_foreign_keys():
        backup_tables(database)
        recode_roots_table(database)
        create_mijlpalen_tables(database)
        init_base_directories(database)
        modify_studenten_table(database)
        correct_student_errors(database)    
        #to recompute insert_students.json and student directories: 
        # 1: set prepare to True
        # 2: run migration: py aapa_migrate.py database_name 1.18 1.19 en 1.19 1.20
        # 3: run the student-import script: py aapa.py -preview --student=studenten.xlsx
        # 4: uncomment the lines
        # 5: run migration again. 
        # 6: check results        
        if phase > 1:
            import_studenten(database, r'.\migrate\m119\insert_students.json')
            correct_student_errors(database, phase_1=False)    
            #to recompute the .json files involved: 
            #see above, but run detect script py aapa.py -preview --detect=base_dir directory (for each base directory)
        if phase > 2:
            import_student_directories(database)
            create_views(database)
            correct_aanvragen_errors(database)
        cleanup_backup(database)

def after_migrate(database_name: str, debug=False, phase=42):
    pass # just testing. To be done later if necessary. Get a clearer way to (re)produce the SQL scripts.

        # 
        