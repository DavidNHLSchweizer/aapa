from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.classes.files import File, Files
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import SDA, StudentDirectory
from data.general.aapa_class import AAPAclass
from main.log import log_info, log_print
from plugins.plugin import PluginBase
from process.general.student_directory_detector import StudentDirectoryDetector
from process.input.importing.dirname_parser import DirectoryNameParser
from process.input.importing.filename_parser import FileTypeDetector
from process.main.aapa_processor import AAPARunnerContext
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries
from storage.queries.student_directories import StudentDirectoryQueries

class SyncException(Exception): pass


class StudentDirectoryCompare(dict):
    class COMPARE(Enum):
        NEW_STUD_DIR = auto()
        DELETED_MP_DIR = auto()
        NEW_MP_DIR = auto()
        DELETED_FILE = auto()
        NEW_FILE = auto()
        CHANGED_FILE = auto()
    def __init__(self):
        for problem in SDC:
            self[problem] = []
    def add(self, problem: SDC, item: AAPAclass):
        self[problem].append(item)
SDC = StudentDirectoryCompare.COMPARE

class StudentDirectoryCompareProcessor:
    def __init__(self):
        self.problems = StudentDirectoryCompare()
    def compare(self, stored_stud_dir: StudentDirectory, actual_stud_dir: StudentDirectory): 
        if not stored_stud_dir:
            self._log_student_directory(actual_stud_dir, 'Nieuwe studentdirectory: ')
            self.problems.add(SDC.NEW_STUD_DIR, actual_stud_dir)
            return 
        assert stored_stud_dir.student == actual_stud_dir.student
        assert str(stored_stud_dir.directory) == str(actual_stud_dir.directory)
        assert stored_stud_dir.base_dir == actual_stud_dir.base_dir
        handled = []
        for stored_mp_dir in stored_stud_dir.directories:
            if (actual_mp_dir := actual_stud_dir.data._find(stored_mp_dir)):
                handled.append(actual_mp_dir)
                self.compare_mp_dirs(stored_mp_dir, actual_mp_dir)
            else:
                self._log_mijlpaal_directory(stored_mp_dir, 'Verwijderde mijlpaaldirectory: ')
                self.problems.add(SDC.DELETED_MP_DIR, stored_mp_dir)
        for actual_mp_dir in actual_stud_dir.directories:
            if not actual_mp_dir in handled:
                self._log_mijlpaal_directory(stored_mp_dir, 'Nieuwe mijlpaaldirectory: ')
                self.problems.add(SDC.NEW_MP_DIR, actual_mp_dir)
    def compare_mp_dirs(self, stored_mp_dir: MijlpaalDirectory, actual_mp_dir: MijlpaalDirectory):
        assert str(stored_mp_dir.directory) == str(actual_mp_dir.directory)
        handled = []
        for stored_file in stored_mp_dir.files.files:
            if (actual_file:=actual_mp_dir.files._find(stored_file)):
                handled.append(actual_file)
                actual_file.ensure_timestamp_and_digest()
                if actual_file.equal_relevant_attributes(stored_file):
                    continue
                else:
                    self._log_file(actual_file, 'Veranderde file: ')
                    self.problems.add(SDC.CHANGED_FILE, actual_file)
            else:
                self._log_file(stored_file, 'Verwijderde file: ')
                self.problems.add(SDC.DELETED_FILE, stored_file)
        for actual_file in actual_mp_dir.files.files:
            if not actual_file in handled:
                self._log_file(actual_file, 'Nieuwe file: ')
                self.problems.add(SDC.NEW_FILE, actual_file)

    def _log_student_directory(self, stud_dir: StudentDirectory, msg=''):
        log_print(f'\t{File.display_file(stud_dir.directory)} {stud_dir.status}')
    def _log_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, msg=''):
        log_print(f'\t{msg}{File.display_file(mp_dir.directory)} ({mp_dir.mijlpaal_type})  kans={mp_dir.kans} datum={mp_dir.datum}')
    def _log_file(self, file: File, msg=''):
        log_print(f'\t{msg}{File.display_file(file.filename)}')
    def dump(self):
        def dump_student_directories(directories: list[StudentDirectory], msg: str):
            log_print(msg)
            for stud_dir in value:
                log_print(f'\t{File.display_file(stud_dir.directory)}')
        def dump_mijlpaal_directories(directories: list[MijlpaalDirectory], msg: str):
            log_print(msg)
            for mp_dir in directories:
                self._log_mijlpaal_directory(mp_dir)
        def dump_files(files: list[File], msg: str):
            log_print(msg)
            for file in files:
                self._log_file(file)
        for key,value in self.problems.items():
            if not value:
                continue
            match key:
                case SDC.NEW_STUD_DIR: 
                    dump_student_directories(value, 'Nieuwe student directories:')
                    for stud_dir in value:
                        self._log_student_directory(stud_dir)
                case SDC.DELETED_MP_DIR:
                    dump_mijlpaal_directories(value,'Verwijderde mijlpaal directories:')
                case SDC.NEW_MP_DIR:
                    dump_mijlpaal_directories(value,'Nieuwe mijlpaal directories:')
                case SDC.DELETED_FILE:
                    dump_files(value, 'Verwijderde files:')
                case SDC.NEW_FILE:
                    dump_files(value, 'Nieuwe files:')
                case SDC.CHANGED_FILE:
                    dump_files(value, 'Veranderde files:')

class BasedirSyncProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.stud_dir_queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        self.detector = StudentDirectoryDetector()
        self.compare_processor = StudentDirectoryCompareProcessor()
    def _init_basedir(self, directory: str)->BaseDir:
        queries: BaseDirQueries = self.storage.queries('base_dirs')
        return queries.find_basedir(directory, start_at_parent=False)
    

    def compare_with_database(self, actual_student_directory: StudentDirectory):
        stored = self.stud_dir_queries.find_student_dir_for_directory(actual_student_directory.student, actual_student_directory.directory)
        self.compare_processor.compare(stored_stud_dir=stored, actual_stud_dir=actual_student_directory)       
    def sync_student_dir(self, directory: str, preview=False)->bool:
        log_info(f'Synchonisatie {File.display_file(directory)}')
        actual_student_dir = self.detector.process(directory,self.storage,True)
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
        
    def process(self, directory: str|list[str], preview=False)->bool:
        if isinstance(directory,str):
            result = self.sync_basedir(directory, preview)
        elif isinstance(directory,list):
            result = True
            for dir in directory:
                if not self.sync_basedir(dir, preview):
                    result = False
            self.compare_processor.dump()

        else:
            raise SyncException(f'Invalid call to process: {directory} must be str or list[str]')
        return result   

class SyncBaseDirPlugin(PluginBase):
    def get_parser(self)->ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--json', dest='json', type=str,help='JSON filename waar SQL output wordt weggeschreven') 
        parser.add_argument('basedir', nargs='*', type=str,help='De basisdirectories om te synchroniseren') 
        return parser
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.processor = BasedirSyncProcessor(context.configuration.storage)
        self.basedirs = kwdargs.get('basedir')
        self.json = kwdargs.get('json')
        if not self.json:
            self.json = 'sync_basedir.json'
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        print('Start running basedir-sync')
        self.processor.process(self.basedirs, context.preview)
        print(self.json)
