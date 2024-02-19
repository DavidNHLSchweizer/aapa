from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import SDA, StudentDirectory
from data.classes.studenten import Student
from data.general.aapa_class import AAPAclass
from data.general.const import UNKNOWN_STUDNR
from data.general.roots import Roots
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from main.log import log_info, log_print
from plugins.plugin import PluginBase
from process.general.student_directory_detector import StudentDirectoryDetector
from process.main.aapa_processor import AAPARunnerContext
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries
from storage.queries.files import FilesQueries
from storage.queries.student_directories import StudentDirectoryQueries

class SyncException(Exception): pass


class StudentDirectoryCompare(dict):
    class COMPARE(Enum):
        NEW_STUD_DIR = auto()
        CHANGED_STUD_DIR = auto()
        DELETED_MP_DIR = auto()
        NEW_MP_DIR = auto()
        CHANGED_MP_DIR = auto()
        DELETED_FILE = auto()
        NEW_FILE = auto()
        CHANGED_FILE = auto()
    def __init__(self):
        for difference in SDC:
            self[difference] = []
    def aapa_items(self, difference: SDC)->list[AAPAclass]:
        return [entry['item'] for entry in self[difference]]
    def add(self, difference: SDC, item: AAPAclass, owner: AAPAclass):
        self[difference].append({'item':item, 'owner': owner})
SDC = StudentDirectoryCompare.COMPARE

class StudentDirectorySQL:
    def __init__(self, storage: AAPAStorage):
        self.storage= storage
        self.sql = self.__init_sql_collectors()
    def __init_sql_collectors(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add('studenten', 
                 SQLcollector(
                {'insert':{'sql':'insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)'},
                }))               
        sql.add('student_directories', 
                 SQLcollector(
                {'insert':{'sql':'insert into STUDENT_DIRECTORIES (id,stud_id,directory,basedir_id,status) values(?,?,?,?,?)'},
                 'update':{'sql':'update STUDENT_DIRECTORIES set stud_id=?,directory=?,basedir_id=?,status=? WHERE id=?'}}))
        sql.add('mijlpaal_directories', 
                 SQLcollector
                 ({'insert':{'sql':'insert into MIJLPAAL_DIRECTORIES (id,mijlpaal_type,kans,directory,datum) values(?,?,?,?,?)'},
                   'update':{'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,kans=?,directory=?,datum=? WHERE id=?'}}))
        sql.add('student_directory_directories', SQLcollector(
            {'insert': {'sql':'insert into STUDENT_DIRECTORY_DIRECTORIES (stud_dir_id,mp_dir_id) values(?,?)'},
             'delete': {'sql':'delete from STUDENT_DIRECTORY_DIRECTORIES where stud_dir_id=? and mp_dir_id=?','concatenate':False}}))
        sql.add('files', SQLcollector(
             {'insert': {'sql':'insert into FILES (id,filename,timestamp,digest,filetype,mijlpaal_type) values(?,?,?,?,?,?)', 'concatenate':False},
              'update': {'sql':'update FILES set filename=?,timestamp=?,digest=?,filetype=?,mijlpaal_type=? WHERE id = ?'},
              'delete': {'sql':'delete from FILES WHERE id in (?)'}}))
        sql.add('mijlpaal_directory_files', SQLcollector(
            {'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES (mp_dir_id,file_id) values(?,?)'},
             'delete': {'sql':'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id in (?)'}}))
        sql.add('mijlpaal_directory_files2', SQLcollector(
            { 'delete': {'sql':'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id=? and file_id=?', 'concatenate':False},}))
        return sql
    def process(self, differences: StudentDirectoryCompare):
        for difference in SDC:
            for entry in differences[difference]:
                item,owner = entry.values()
                match difference:
                    case SDC.NEW_STUD_DIR: 
                        self._handle_new_student_directory(item)
                    case SDC.CHANGED_STUD_DIR: 
                        self._handle_changed_student_directory(item)
                    case SDC.NEW_MP_DIR: 
                        self._handle_new_mijlpaal_directory(item, owner)                
                    case SDC.CHANGED_MP_DIR: 
                        self._handle_changed_mijlpaal_directory(item)                
                    case SDC.DELETED_MP_DIR: 
                        self._handle_deleted_mijlpaal_directory(item,owner)                
                    case SDC.DELETED_FILE:
                        self._handle_deleted_file(item, owner)
                    case SDC.CHANGED_FILE:
                        self._handle_changed_file(item, owner)
                    case SDC.NEW_FILE:
                        self._handle_new_file(item, owner)
                    case _: raise SyncException('Vergeten dit ook op te geven....')
    def _handle_new_student_directory(self, stud_dir: StudentDirectory):
        self.sql.insert('student_directories', [stud_dir.id, stud_dir.student.id, Roots.encode_path(stud_dir.directory), stud_dir.base_dir.id,stud_dir.status])
    def _handle_changed_student_directory(self, stud_dir: StudentDirectory):
        self.sql.update('student_directories', [stud_dir.student.id, Roots.encode_path(stud_dir.directory), stud_dir.base_dir.id,stud_dir.status, stud_dir.id])
    def _handle_deleted_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, owner_stud_dir: StudentDirectory):
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
        self.sql.delete('student_directory_directories', [owner_stud_dir.id, mp_dir.id])
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
    def _handle_changed_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self.sql.update('mijlpaal_directories', [mp_dir.mijlpaal_type, mp_dir.kans, 
                                                 Roots.encode_path(mp_dir.directory), 
                                                 TSC.timestamp_to_sortable_str(mp_dir.datum),mp_dir.id])
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
    def _handle_new_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, owner_stud_dir: StudentDirectory):
        self.sql.insert('mijlpaal_directories', [mp_dir.id, mp_dir.mijlpaal_type, mp_dir.kans, 
                                                 Roots.encode_path(mp_dir.directory), 
                                                 TSC.timestamp_to_sortable_str(mp_dir.datum)])
        self.sql.insert('student_directory_directories', [owner_stud_dir.id, mp_dir.id])
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
    def _handle_new_file(self, file: File, owner_mp_dir: MijlpaalDirectory):
        self.sql.insert('files', [file.id, Roots.encode_path(file.filename),TSC.timestamp_to_sortable_str(file.timestamp),
                                  file.digest,file.filetype,file.mijlpaal_type])
        self.sql.insert('mijlpaal_directory_files', [owner_mp_dir.id,file.id])
    def _handle_changed_file(self, file: File, owner_mp_dir:MijlpaalDirectory):        
        self.sql.update('files', [Roots.encode_path(file.filename),TSC.timestamp_to_sortable_str(file.timestamp),
                                  file.digest,file.filetype,file.mijlpaal_type,file.id])
        if owner_mp_dir:
            self.sql.insert('mijlpaal_directory_files', [owner_mp_dir.id,file.id])

    def _handle_deleted_file(self, file: File, owner_mp_dir: MijlpaalDirectory):
        self.sql.delete('files', [file.id])
        self.sql.delete('mijlpaal_directory_files2', [owner_mp_dir.id, file.id])
    def add_new_student(self, student: Student):
        self.storage.ensure_key('studenten', student)
        self.sql.insert('studenten', [student.id,UNKNOWN_STUDNR,student.full_name,student.first_name,student.email,student.status])
        
class StudentDirectoryCompareProcessor:
    def __init__(self, storage: AAPAStorage):
        self.differences = StudentDirectoryCompare()
        self.storage=storage
    def _file_is_already_known(self, file: File)->bool:
        #there are some files in the system that are not coupled to a MijlpaalDirectory
        queries: FilesQueries = self.storage.queries('files')
        return queries.find_values('filename', Roots.encode_path(file.filename)) != []
    def _add_new_files(self, actual_mp_dir: MijlpaalDirectory, store_in_dir: MijlpaalDirectory, handled: list[File] = []):
        for actual_file in actual_mp_dir.files.files:
            if actual_file in handled:
                continue
            if self._file_is_already_known(actual_file):
                #this could happen if the file was already known but not coupled to the mp_dir
                self._log_file(actual_file, 'Veranderde file (in mijlpaaldirectory): ')
                self.differences.add(SDC.CHANGED_FILE, actual_file, store_in_dir)                
            else:
                self._log_file(actual_file, 'Nieuwe file: ')
                self.differences.add(SDC.NEW_FILE, actual_file, store_in_dir)
    def _add_new_student_directory(self, stud_dir: StudentDirectory):            
        self._log_student_directory(stud_dir, 'Nieuwe studentdirectory: ')
        stud_dir.status = StudentDirectory.Status.ACTIVE
        self.differences.add(SDC.NEW_STUD_DIR, stud_dir, None)
        for mp_dir in stud_dir.directories:
            mp_dir.ensure_datum()
            self._add_new_mijlpaal_directory(mp_dir, stud_dir)
        #also update status for any older directories
        queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        for old_stud_dir in queries.find_student_dirs(stud_dir.student):
            if old_stud_dir.status != StudentDirectory.Status.ARCHIVED:
                old_stud_dir.status = StudentDirectory.Status.ARCHIVED
                self.differences.add(SDC.CHANGED_STUD_DIR, old_stud_dir, None)
    def _add_new_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, owner_stud_dir:StudentDirectory):
        self._log_mijlpaal_directory(mp_dir, 'Nieuwe mijlpaaldirectory: ')
        self.differences.add(SDC.NEW_MP_DIR, mp_dir, owner_stud_dir)
        self._add_new_files(mp_dir,mp_dir)
    def compare(self, stored_stud_dir: StudentDirectory, actual_stud_dir: StudentDirectory): 
        if not stored_stud_dir:
            self._add_new_student_directory(actual_stud_dir)
            return 
        assert stored_stud_dir.student == actual_stud_dir.student
        assert str(stored_stud_dir.directory).lower() == str(actual_stud_dir.directory).lower()
        assert stored_stud_dir.base_dir == actual_stud_dir.base_dir
        handled = []
        for stored_mp_dir in stored_stud_dir.directories:
            if (actual_mp_dir := actual_stud_dir.data._find(stored_mp_dir)):
                handled.append(actual_mp_dir)
                actual_mp_dir.ensure_datum()
                if not actual_mp_dir.equal_relevant_attributes(stored_mp_dir):                    
                    self._log_mijlpaal_directory(stored_mp_dir, 'Veranderde mijlpaaldirectory:')
                    actual_mp_dir.id=stored_mp_dir.id # else there might be a new mp_dir id involved
                    self.differences.add(SDC.CHANGED_MP_DIR, actual_mp_dir, stored_stud_dir)
                self.compare_mp_dirs(stored_mp_dir, actual_mp_dir)
            else:
                self._log_mijlpaal_directory(stored_mp_dir, 'Verwijderde mijlpaaldirectory: ')
                self.differences.add(SDC.DELETED_MP_DIR, stored_mp_dir, stored_stud_dir)
        for actual_mp_dir in actual_stud_dir.directories:
            if not actual_mp_dir in handled:
                self._add_new_mijlpaal_directory(actual_mp_dir, stored_stud_dir)
    def compare_mp_dirs(self, stored_mp_dir: MijlpaalDirectory, actual_mp_dir: MijlpaalDirectory):
        assert str(stored_mp_dir.directory).lower() == str(actual_mp_dir.directory).lower()
        handled:list[File] = []
        for stored_file in stored_mp_dir.files.files:
            if (actual_file:=actual_mp_dir.files._find(stored_file)):
                handled.append(actual_file)
                actual_file.ensure_timestamp_and_digest()
                if actual_file.equal_relevant_attributes(stored_file):
                    continue
                else:
                    self._log_file(stored_file, 'Veranderde file: ')
                    actual_file.id=stored_file.id # actual file might have new id
                    self.differences.add(SDC.CHANGED_FILE, actual_file, None)
            else:
                self._log_file(stored_file, 'Verwijderde file: ')
                self.differences.add(SDC.DELETED_FILE, stored_file, stored_mp_dir)
        self._add_new_files(actual_mp_dir, stored_mp_dir, handled)
    def _log_student_directory(self, stud_dir: StudentDirectory, msg=''):
        log_print(f'\t{msg}{File.display_file(stud_dir.directory)} [{stud_dir.status}]')
    def _log_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, msg=''):
        log_print(f'\t{msg}{File.display_file(mp_dir.directory)} ({mp_dir.mijlpaal_type})  kans={mp_dir.kans} datum={TSC.get_date_str(mp_dir.datum)}')
    def _log_file(self, file: File, msg=''):
        log_print(f'\t{msg}{File.display_file(file.filename)}')
    def dump(self, new_students: list[Student]=None):
        def dump_studenten(studenten: list[Student], msg: str):
            log_print(msg)
            for student in studenten:
                log_print(f'\t{student}')            
        def dump_student_directories(stud_dirs: list[StudentDirectory], msg: str):
            log_print(msg)
            for stud_dir in stud_dirs:
                log_print(f'\t{File.display_file(stud_dir.directory)}')
        def dump_mijlpaal_directories(directories: list[MijlpaalDirectory], msg: str):
            log_print(msg)
            for mp_dir in directories:
                self._log_mijlpaal_directory(mp_dir)
        def dump_files(files: list[File], msg: str):
            log_print(msg)
            for file in files:
                self._log_file(file)            
        if new_students:
            dump_studenten(new_students, 'Nieuwe studenten:')
        for key in SDC:
            items = self.differences.aapa_items(key)
            if not items: continue
            match key:
                case SDC.NEW_STUD_DIR: 
                    dump_student_directories(items, 'Nieuwe student directories:')
                case SDC.CHANGED_STUD_DIR:
                    dump_student_directories(items, 'Veranderde student directories:')
                case SDC.DELETED_MP_DIR:
                    dump_mijlpaal_directories(items, 'Verwijderde mijlpaal directories:')
                case SDC.NEW_MP_DIR:
                    dump_mijlpaal_directories(items,'Nieuwe mijlpaal directories:')
                case SDC.DELETED_FILE:
                    dump_files(items, 'Verwijderde files:')
                case SDC.NEW_FILE:
                    dump_files(items, 'Nieuwe files:')
                case SDC.CHANGED_FILE:
                    dump_files(items, 'Veranderde files:')
                case _: raise SyncException(f'Vergeten SDCP:{key}')

class BasedirSyncProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.stud_dir_queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        self.detector = StudentDirectoryDetector()
        self.compare_processor = StudentDirectoryCompareProcessor(storage)
        self.sql_processor = StudentDirectorySQL(storage)
        self.new_students = []
    def _init_basedir(self, directory: str)->BaseDir:
        queries: BaseDirQueries = self.storage.queries('base_dirs')
        return queries.find_basedir(directory, start_at_parent=False)
    def dump_sql(self, json_file: str):
        self.sql_processor.sql.dump_to_file(json_file)
    def compare_with_database(self, actual_student_directory: StudentDirectory):
        stored = self.stud_dir_queries.find_student_dir_for_directory(actual_student_directory.student, actual_student_directory.directory)
        self.compare_processor.compare(stored_stud_dir=stored, actual_stud_dir=actual_student_directory)       
        self.sql_processor.process(self.compare_processor.differences)
    def add_new_student_and_directory(self, new_student_dir: StudentDirectory):
        self.sql_processor.add_new_student(new_student_dir.student)
        self.new_students.append(new_student_dir.student)
        # self.compare_processor.compare(None, new_student_dir)
    def sync_student_dir(self, directory: str, preview=False)->bool:
        log_info(f'Synchronisatie {File.display_file(directory)}')
        actual_student_dir = self.detector.process(directory,self.storage,True)
        if self.detector.is_new_student(actual_student_dir.student):
            self.add_new_student_and_directory(actual_student_dir)
        self.compare_with_database(actual_student_dir)
    def sync_basedir(self, directory: str, preview=False)->bool:
        if not (basedir := self._init_basedir(directory)):
            return False
        log_info(f'Synchroniseren basisdirectory {File.display_file(directory)}', to_console=True)        
        for directory in Path(basedir.directory).glob('*'):
            if not directory.is_dir() or (not BaseDir.is_student_directory_name(directory)):
                continue
            self.sync_student_dir(directory)
        print('-------------------')        
    def process(self, directory: str|list[str], preview=False, verbose=False)->bool:
        if isinstance(directory,str):
            result = self.sync_basedir(directory, preview)
        elif isinstance(directory,list):
            result = True
            for dir in directory:
                if not self.sync_basedir(dir, preview):
                    result = False
            if verbose:
                self.compare_processor.dump(self.new_students)
        else:
            raise SyncException(f'Invalid call to process: {directory} must be str or list[str]')
        return result   

class SyncBaseDirPlugin(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        parser.add_argument('--basedir', nargs='+', action='append', type=str, help='De basisdirectory (of -directories) om te synchroniseren') 
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.processor = BasedirSyncProcessor(context.storage)
        self.basedirs = [Roots.decode_onedrive(bd) for bd in self._unlistify(kwdargs.get('basedir'))]
        self.json = kwdargs.get('json')
        if not self.json:
            self.json = 'sync_basedir.json'
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        print('Start running basedir-sync')
        self.processor.process(self.basedirs, context.preview)
        self.processor.dump_sql(self.json)
        print(f'sql dumped to {self.json}')
