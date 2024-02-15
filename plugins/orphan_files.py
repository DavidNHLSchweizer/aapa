from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
from pathlib import Path
import re
from data.classes.base_dirs import BaseDir
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import SDA, StudentDirectory
from data.classes.studenten import Student
from data.general.aapa_class import AAPAclass
from data.general.roots import Roots
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from main.log import log_error, log_info, log_print
from plugins.plugin import PluginBase
from process.general.student_directory_detector import StudentDirectoryDetector
from process.input.importing.dirname_parser import DirectoryNameParser
from process.main.aapa_processor import AAPARunnerContext
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries
from storage.queries.files import FilesQueries
from storage.queries.student_directories import StudentDirectoryQueries
from storage.queries.studenten import StudentQueries

class OrphanException(Exception): pass


class StudentDirectoryCompare(dict):
    class COMPARE(Enum):
        NEW_STUD_DIR = auto()
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
        sql.add('student_directories', 
                 SQLcollector(
                {'insert':{'sql':'insert into STUDENT_DIRECTORIES (id,stud_id,directory,basedir_id,status) values(?,?,?,?)'},}))
        sql.add('mijlpaal_directories', 
                 SQLcollector
                 ({'insert':{'sql':'insert into MIJLPAAL_DIRECTORIES (id,mijlpaal_type,kans=?,directory,datum) values(?,?,?,?)'},
                   'update':{'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,kans=?,directory=?,datum=? WHERE id=?'}}))
        sql.add('student_directory_directories', SQLcollector(
            {'insert': {'sql':'insert into STUDENT_DIRECTORY_DIRECTORIES (stud_dir_id,mp_dir_id) values(?,?)'},
             'delete': {'sql':'delete from STUDENT_DIRECTORY_DIRECTORIES where stud_dir_id=? and mp_dir_id=?','concatenate':False}}))
        sql.add('files', SQLcollector(
             {'insert': {'sql':'insert into FILES (id,filename,timestamp,digest,filetype,mijlpaal_type) values(?,?,?,?,?,?)'},
              'update': {'sql':'update FILES set filename=?,timestamp=?,digest=?,filetype=?,mijlpaal_type=? WHERE id = ?'},
              'delete': {'sql':'delete from FILES WHERE id in (?)'}}))
        sql.add('mijlpaal_directory_files', SQLcollector(
            {'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES (mp_dir_id,file_id) values(?,?)',
             'delete': {'sql':'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id in (?)'}}}))
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
                    case SDC.NEW_MP_DIR: 
                        self._handle_new_mijlpaal_directory(item, owner)                
                    case SDC.CHANGED_MP_DIR: 
                        self._handle_changed_mijlpaal_directory(item)                
                    case SDC.DELETED_MP_DIR: 
                        self._handle_deleted_mijlpaal_directory(item,owner)                
                    case SDC.DELETED_FILE:
                        self._handle_deleted_file(item, owner)
                    case SDC.CHANGED_FILE:
                        self._handle_changed_file(item)
                    case SDC.NEW_FILE:
                        self._handle_new_file(item, owner)
                    case _: raise SyncException('Vergeten dit ook op te geven....')
    def _handle_new_student_directory(self, stud_dir: StudentDirectory):
        self.sql.insert('student_directories', [stud_dir.id, stud_dir.student.id, Roots.encode_path(stud_dir.directory), stud_dir.base_dir.id,stud_dir.status])
        for mp_dir in stud_dir.directories:
            self.sql.insert('student_directory_directories', [stud_dir.id, mp_dir.id])
    def _handle_deleted_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, stud_dir: StudentDirectory):
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
        self.sql.delete('student_directory_directories', [stud_dir.id, mp_dir.id])
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
    def _handle_changed_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self.sql.update('mijlpaal_directories', [mp_dir.mijlpaal_type, mp_dir.kans, 
                                                 Roots.encode_path(mp_dir.directory), 
                                                 TSC.timestamp_to_sortable_str(mp_dir.datum),mp_dir.id])
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
    def _handle_new_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, stored_stud_dir: StudentDirectory):
        self.sql.insert('mijlpaal_directories', [mp_dir.id, mp_dir.mijlpaal_type, mp_dir.kans, 
                                                 Roots.encode_path(mp_dir.directory), 
                                                 TSC.timestamp_to_sortable_str(mp_dir.datum)])
        self.sql.insert('student_directory_directories', [stored_stud_dir.id, mp_dir.id])
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
    def _handle_new_file(self, file: File, mp_dir: MijlpaalDirectory):
        self.sql.insert('files', [file.id, Roots.encode_path(file.filename),TSC.timestamp_to_sortable_str(file.timestamp),
                                  file.digest,file.filetype,file.mijlpaal_type])
        self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
    def _handle_changed_file(self, file: File):
        self.sql.update('files', [Roots.encode_path(file.filename),TSC.timestamp_to_sortable_str(file.timestamp),
                                  file.digest,file.filetype,file.mijlpaal_type,file.id])
    def _handle_deleted_file(self, file: File, mp_dir: MijlpaalDirectory):
        self.sql.delete('files', [file.id])
        self.sql.delete('mijlpaal_directory_files2', [mp_dir.id, file.id])

class StudentDirectoryCompareProcessor:
    def __init__(self, storage: AAPAStorage):
        self.differences = StudentDirectoryCompare()
        self.storage=storage
    def _file_is_already_known(self, file: File)->bool:
        #there are some files in the system that are not coupled to a MijlpaalDirectory
        queries: FilesQueries = self.storage.queries('files')
        return queries.find_values('filename', Roots.encode_path(file.filename)) is []
    def add_new_files(self, actual_mp_dir: MijlpaalDirectory, store_in_dir: MijlpaalDirectory, handled: list[File] = []):
        for actual_file in actual_mp_dir.files.files:
            if not (actual_file in handled or self._file_is_already_known(actual_file)):
                self._log_file(actual_file, 'Nieuwe file: ')
                self.differences.add(SDC.NEW_FILE, actual_file, store_in_dir)
    def compare(self, stored_stud_dir: StudentDirectory, actual_stud_dir: StudentDirectory): 
        if not stored_stud_dir:
            self._log_student_directory(actual_stud_dir, 'Nieuwe studentdirectory: ')
            self.differences.add(SDC.NEW_STUD_DIR, actual_stud_dir, None)
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
                    self._log_mijlpaal_directory(actual_mp_dir, 'Veranderde mijlpaaldirectory:')
                    self.differences.add(SDC.CHANGED_MP_DIR, actual_mp_dir, stored_stud_dir)
                self.compare_mp_dirs(stored_mp_dir, actual_mp_dir)
            else:
                self._log_mijlpaal_directory(stored_mp_dir, 'Verwijderde mijlpaaldirectory: ')
                self.differences.add(SDC.DELETED_MP_DIR, stored_mp_dir, stored_stud_dir)
        for actual_mp_dir in actual_stud_dir.directories:
            if not actual_mp_dir in handled:
                self._log_mijlpaal_directory(stored_mp_dir, 'Nieuwe mijlpaaldirectory: ')
                self.differences.add(SDC.NEW_MP_DIR, actual_mp_dir, stored_stud_dir)
                self.add_new_files(actual_mp_dir, actual_mp_dir)
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
                    self._log_file(actual_file, 'Veranderde file: ')
                    self.differences.add(SDC.CHANGED_FILE, actual_file, stored_mp_dir)
            else:
                self._log_file(stored_file, 'Verwijderde file: ')
                self.differences.add(SDC.DELETED_FILE, stored_file, stored_mp_dir)
        self.add_new_files(actual_mp_dir, stored_mp_dir, handled)
    def _log_student_directory(self, stud_dir: StudentDirectory, msg=''):
        log_print(f'\t{File.display_file(stud_dir.directory)} [{stud_dir.status}]')
    def _log_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, msg=''):
        log_print(f'\t{msg}{File.display_file(mp_dir.directory)} ({mp_dir.mijlpaal_type})  kans={mp_dir.kans} datum={mp_dir.datum}')
    def _log_file(self, file: File, msg=''):
        log_print(f'\t{msg}{File.display_file(file.filename)}')
    def dump(self):
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
        for key in SDC:
            items = self.differences.aapa_items(key)
            if not items: continue
            match key:
                case SDC.NEW_STUD_DIR: 
                    dump_student_directories(items, 'Nieuwe student directories:')
                    for stud_dir in items:
                        self._log_student_directory(stud_dir)
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

class OrphanFileProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.database = storage.database
        self.file_queries: FilesQueries = self.storage.queries('files')
        self.student_queries: StudentQueries = self.storage.queries('studenten')
        self.sql_processor = StudentDirectorySQL(storage)
        self.skip_pattern = re.compile(r"Beoordeling aanvragen 2023\\Week\s\d")
        self.parser = DirectoryNameParser()
    def _get_student(self,filename: str)->Student:
        if not (parsed := self.parser.parsed(Path(filename).parent)):
            raise OrphanException(f'directory {File.display_file(filename)} kan niet worden geanalyseerd.')
        tem_student = Student(full_name=parsed.student,email=parsed.email())
        if not (stored := self.student_queries.find_student_by_name_or_email_or_studnr(tem_student)):
            raise OrphanException(f'Student kan niet worden gevonden voor wees-file {File.display_file(filename)}')
        return stored
    def _get_mijlpaal_dir(self, filename: str)->MijlpaalDirectory:
        if (rows:=self.storage.queries('mijlpaal_directories').find_values('directory', Roots.encode_path(Path(filename).parent))):
            return rows[0]
        return None
    def _is_in_beoordeling_aanvraag_directory_2023(self, filename: str)->bool:
        return self.skip_pattern.search(filename) is not None
    def handle_file(self, file: File)->bool:
        if self._is_in_beoordeling_aanvraag_directory_2023(file.filename):
            return True
        try:
            student = self._get_student(file.filename)
            if student.status in {Student.Status.AFGESTUDEERD,Student.Status.GESTOPT}:
                return True
            mijlpaal_dir = self._get_mijlpaal_dir(file.filename)
            print(f'{student}:{File.display_file(file.filename)}')
            if not mijlpaal_dir: 
                print('no shit')
            else:
                print(f'\t{File.display_file(mijlpaal_dir.directory)}')
            return True
        except OrphanException as E:
            log_error(f'Bestand {File.display_file(file.filename)} kan niet aan student worden gekoppeld.')    
            return False
        
    def process(self, preview=False)->bool:
        query = f'select id from FILES as F where not exists (select * from MIJLPAAL_DIRECTORY_FILES where file_id = F.id) and not F.filetype in (?,?,?,?,?)'        
        if rows:=self.database._execute_sql_command(query, [File.Type.INVALID_DOCX, File.Type.INVALID_PDF, File.Type.COPIED_PDF,File.Type.DIFFERENCE_HTML, File.Type.GRADE_FORM_DOCX], True):
            orphan_files = list(filter(lambda f: Roots.is_on_onedrive(f.filename), self.storage.read_many('files', {row['id'] for row in rows})))
        else:
            orphan_files = []
        for orphan in orphan_files:             
            self.handle_file(orphan)
        print(f'{len(orphan_files)} files')
        return True

class OrphanFilesPlugin(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.processor = OrphanFileProcessor(context.configuration.storage)
        self.json = kwdargs.get('json')
        if not self.json:
            self.json = 'orphan_files.json'
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        print('Start running orphan-files')
        self.processor.process(context.preview)
        self.processor.sql_processor.sql.dump_to_file(self.json)
        print(f'sql dumped to {self.json}')
