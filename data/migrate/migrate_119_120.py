from typing import Tuple
from data.aapa_database import AAPaDatabase, BaseDirsTableDefinition, StudentAanvragenTableDefinition, StudentMilestonesTableDefinition, StudentVerslagenTableDefinition, VerslagFilesTableDefinition, VerslagTableDefinition, create_roots, load_roots
from data.classes.base_dirs import BaseDir
from data.classes.files import File
from data.migrate.old_119.roots import old_add_root, old_decode_path, old_reset_roots
from data.roots import ONEDRIVE, add_root, decode_path, encode_path, get_onedrive_root, get_roots, reset_roots
from data.storage.aapa_storage import AAPAStorage
from database.database import Database
from database.sql_table import SQLcreateTable
from database.table_def import TableDefinition
import database.dbConst as dbc
from general.keys import reset_key
from general.timeutil import TSC

# recoding all fileroots 
# toevoegen VERSLAGEN tabel en BASEDIRS tabel
# toevoegen STUDENT_MILESTONES en STUDENT_MILESTONES_DETAILS tabel

def create_verslagen_tables(database: Database):
    print('toevoegen nieuwe tabel VERSLAGEN en VERSLAG_FILES')
    database.execute_sql_command(SQLcreateTable(VerslagTableDefinition()))
    database.execute_sql_command(SQLcreateTable(VerslagFilesTableDefinition()))
    print('toevoegen nieuwe STUDENT_MILESTONES, STUDENT_AANVRAGEN en STUDENT_VERSLAGEN tabellen')
    database.execute_sql_command(SQLcreateTable(StudentMilestonesTableDefinition()))             
    database.execute_sql_command(SQLcreateTable(StudentAanvragenTableDefinition())) 
    database.execute_sql_command(SQLcreateTable(StudentVerslagenTableDefinition())) 
    print('--- klaar toevoegen nieuwe tabellen')

def init_base_directories(database: Database):
    known_bases = [
               BaseDir(2020, '1', 'v2.2b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1'),
               BaseDir(2020, '1B', 'v2.2b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B'),
               BaseDir(2020, '2', 'v2.2b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2'),
               BaseDir(2021, '1', 'v2.3b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1'),
               BaseDir(2021, '2', 'v2.3b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2'),
               BaseDir(2021, '3', 'v2.3b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3'),
               BaseDir(2021, '4', 'v2.3b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4'),
               BaseDir(2022, '1', 'v3.0.0b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1'),
               BaseDir(2022, '2', 'v4.0.0b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2'),
               BaseDir(2022, '3', 'v4.0.0b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3'),
               BaseDir(2022, '4', 'v4.0.0b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4'),
               BaseDir(2023, '1', 'v4.0.0b', fr'{ONEDRIVE}\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024') 
    ]
    print('adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))
    print('initialisation values BASEDIRS')  
    storage = AAPAStorage(database)
    load_roots(database)
    for entry in known_bases:
        storage.add_file_root(entry.directory.replace('ONEDRIVE:', get_onedrive_root()))
        database._execute_sql_command(
            "insert into BASEDIRS('year', 'period', 'forms_version', 'directory') values (?,?,?,?)", 
            [entry.year, entry.period, entry.forms_version, encode_path(entry.directory)])        
    print('--- ready adding new table BASEDIRS')
    database.execute_sql_command(SQLcreateTable(BaseDirsTableDefinition()))


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
    for root in known_roots:
        add_root(rf'{root}')

def _find_old_roots(database: Database)->list[Tuple[str,str]]:
    result = []
    old_reset_roots()
    reset_key('ROOT')
    for row in database._execute_sql_command(f'select code,root from BACKUP_FILEROOT', return_values=True):
        root = old_decode_path(row['root'])
        new=old_add_root(root)
        # print(f'{new}: {root}')
        result.append((row['code'], root))  
    with open('OLD_ROOTS.txt', 'w', encoding='utf-8') as file:
        file.writelines([f'{code}={value}\n' for code,value in result])
    return result

def _find_unused_roots(database: Database)->list[str]:
    sql = 'select b1.code from backup_fileroot as b1 where (not exists (select filename from BACKUP_files where instr(filename,b1.code) > 0)) AND (not exists (select b2.root from backup_fileroot as b2 where instr(b2.root,b1.code) > 0))'
    result = []
    for row in database._execute_sql_command(sql, return_values=True):
        result.append(row['code'])
    return result

def _find_old_files(database: Database)->list[File]:
    result = []
    for row in database._execute_sql_command(f'select id,filename from BACKUP_FILES', return_values=True):
        result.append((row['id'], old_decode_path(row['filename'])))
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
    onedrive_root = str(get_onedrive_root()) + "\\"
    unused_roots = _find_unused_roots(database)
    for code,root in old_roots[2:]:
        if code in unused_roots:
            continue
        # if root.find(onedrive_root) == 0:
        #     root = root.replace(onedrive_root, ONEDRIVE)
        add_root(root)
    database._execute_sql_command('DELETE from FILEROOT')
    create_roots(database)
    print('update FILES table')
    for id,filename in old_files:  
        old = filename
        # if filename.find(onedrive_root) == 0:
        #     filename = filename[len(onedrive_root)+1:]
        if id < 3:
            encoded = encode_path(filename)
            decoded = decode_path(encoded)
            print(f'{old}\n\t{encoded}\n\t{decoded}')
        database._execute_sql_command("update FILES set filename=? where id = ?", 
                                      [encode_path(filename), id])
    database.commit()
    # _check_results(old_files, _find_all_files(database))

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

def migrate_database(database: Database):
    with database.pause_foreign_keys():
        backup_tables(database)
        recode_roots_table(database)
        # create_verslagen_tables(database)
        # recode_files_table(database)
        # init_base_directories(database)
