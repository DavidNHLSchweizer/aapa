from typing import Tuple
from data.aapa_database import BaseDirsTableDefinition, \
    StudentDirectoryTableDefinition, StudentDirectoryAanvragenTableDefinition, StudentDirectoryVerslagenTableDefinition, \
        VerslagFilesTableDefinition, VerslagTableDefinition, create_roots
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from data.migrate.m119.old_roots import old_add_root, old_decode_path, old_reset_roots
from data.migrate.sql_coll import SQLcollType, SQLcollector
from data.roots import OneDriveCoder, add_root, encode_path, get_onedrive_root, reset_roots
from data.storage.aapa_storage import AAPAStorage
from database.database import Database
from database.sql_table import SQLcreateTable
from database.table_def import TableDefinition
import database.dbConst as dbc
from general.keys import reset_key

# recoding all fileroots 
# toevoegen VERSLAGEN tabel en BASEDIRS tabel
# add status column to STUDENTEN
# toevoegen STUDENT_DIRECTORY 
#   en gerelateerde details STUDENT_DIRECTORY_AANVRAGEN,STUDENT_DIRECTORY_VERSLAGEN tabellen

def _update_roots_table(database:Database):        
    database._execute_sql_command('DELETE from FILEROOT')
    create_roots(database)

def create_verslagen_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN en VERSLAG_FILES')
    database.execute_sql_command(SQLcreateTable(VerslagTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagFilesTableDefinition()))
    print('toevoegen nieuwe STUDENT_DIRECTORY, STUDENT_DIRECTORY_AANVRAGEN en STUDENT_DIRECTORY_VERSLAGEN tabellen')
    database.execute_sql_command(SQLcreateTable(StudentDirectoryTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(StudentDirectoryAanvragenTableDefinition())) 
    database.execute_sql_command(SQLcreateTable(StudentDirectoryVerslagenTableDefinition())) 
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
               BaseDir(2023, '1', 'v4.0.0b', r'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024') 
    ]
    print('adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    print('initialisation values BASEDIRS')  
    for entry in known_bases:
        code=add_root(fr'{OneDriveCoder.ONEDRIVE}\{entry.directory}')
        database._execute_sql_command(
            "insert into BASEDIRS('year', 'period', 'forms_version', 'directory') values (?,?,?,?)", 
            [entry.year, entry.period, entry.forms_version, code])        
    print('--- ready adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    _update_roots_table(database)

def _start_with_new_roots(database: Database):
    known_roots = [rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Beoordeling aanvragen 2023',
                   rf'NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024\Beoordeling aanvragen 2023',
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
    with open('OLD_FILES.txt', 'w', encoding='utf-8') as file:
        file.writelines(f'{str(f)}\n' for f in result)
    return result

def _find_all_files(database:Database):
    storage = AAPAStorage(database)
    result= [(file.id, file.filename) for file in storage.find_all('files')]
    with open('NEW_FILES.txt', 'w', encoding='utf-8') as file:
        file.writelines(f'{str(f)}\n' for f in result)
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

def correct_student_errors(database: Database, phase_1=True):
    if phase_1:
        print('correcting some existing errors in STUDENTEN table')  
    
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
        print('--- klaar correcting some errors in STUDENTEN table')        
    else:    
        print('correcting migration errors in STUDENTEN table')

        #Jimi/Cassandra van Oosten
        database._execute_sql_command(f'update AANVRAGEN set stud_id=? where stud_id = ?', 
                                    [151, 32])
        database._execute_sql_command(f'delete from STUDENTEN where id = ?', [32])

        #Nando Reij, Ramon Booi, Michael Koopmans, Sander Beijaard, Jarno van der Poll, Micky Cheng, Nick Westerdijk, Daniel Roskam, Daan Eekhof
        database._execute_sql_command(f'update STUDENTEN set STATUS=? where stud_nr in (?,?,?,?,?,?,?,?,?,?,?)', 
                                    [Student.Status.BEZIG, '4700082', '4547055','4692012','4621646','3341517','3484695','4699475','4511484','3432962','3541141','3472190'])
        #Robert Slomp, Nam Nguyen  
        database._execute_sql_command(f'update STUDENTEN set STATUS=? where stud_nr in (?,?)', 
                                    [Student.Status.GESTOPT, '3417904', '4621646'])
        print('--- klaar correcting overige errors in STUDENTEN table')


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

def backup_tables(database: Database):
    database.execute_sql_command(SQLcreateTable(BackupFileRootTableDefinition()))
    database._execute_sql_command('insert into BACKUP_FILEROOT SELECT * from FILEROOT')
    database.execute_sql_command(SQLcreateTable(BackupFilesTableDefinition()))
    database._execute_sql_command('insert into BACKUP_FILES SELECT * from FILES')

def cleanup_backup(database: Database):
    database._execute_sql_command('drop table BACKUP_FILEROOT')
    database._execute_sql_command('drop table BACKUP_FILES')

def import_studenten(database: Database, json_name: str):
    print('Importeren nieuwe studenten vanuit lijst')
    sqlcoll = SQLcollector.read_from_dump(json_name)
    for sql_type in SQLcollType:
        collector = sqlcoll.collectors(sql_type)
        sql_str = collector.sql_str
        for params in collector.values:
            database._execute_sql_command(sql_str,parameters=params)
    print('--- klaar importeren nieuwe studenten')

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        backup_tables(database)
        recode_roots_table(database)
        create_verslagen_tables(database)
        init_base_directories(database)
        modify_studenten_table(database)
        correct_student_errors(database)
        import_studenten(database, r'.\data\migrate\m119\insert_students.json')
        correct_student_errors(database, False)
        cleanup_backup(database)
