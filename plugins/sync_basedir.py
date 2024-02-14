from argparse import ArgumentParser
from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.classes.files import File, Files
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import SDA, StudentDirectory
from main.log import log_info
from plugins.plugin import PluginBase
from process.general.student_directory_detector import StudentDirectoryDetector
from process.input.importing.dirname_parser import DirectoryNameParser
from process.input.importing.filename_parser import FileTypeDetector
from process.main.aapa_processor import AAPARunnerContext
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirQueries
from storage.queries.student_directories import StudentDirectoryQueries

class SyncException(Exception): pass

class BasedirSyncProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.stud_dir_queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        self.detector = StudentDirectoryDetector()
    def _init_basedir(self, directory: str)->BaseDir:
        queries: BaseDirQueries = self.storage.queries('base_dirs')
        return queries.find_basedir(directory, start_at_parent=False)
    def _print_mp_dir_diff(self, stored: StudentDirectory, different_mp_dir: MijlpaalDirectory, msg: str):
        print(msg)
        stored_mp = stored.data._find(different_mp_dir)
        if not stored_mp: 
            print(f'{different_mp_dir} not found in mp_data....')
        else:
            print(f'{File.display_file(stored_mp.directory)} {File.display_file(different_mp_dir.directory)}')
    def _print_file_diff(self, stored: StudentDirectory, files: list[File], msg: str):
        if not files:
            return
        print(msg)
        for file in files:
            print(f'\t{File.display_file(file.filename)}')
    def _print_dir_diff(self, stored: StudentDirectory, diff_dict: dict): 
        if diff_dict[SDA.DIFF.EXTRA]:
            for mp_dir in diff_dict[SDA.DIFF.EXTRA]:
                self._print_mp_dir_diff(stored, mp_dir, 'Extra directories')
        if diff_dict[SDA.DIFF.MISSING]:
            for mp_dir in diff_dict[SDA.DIFF.MISSING]:
                self._print_mp_dir_diff(stored, mp_dir, 'Missing directories')
        if diff_dict[SDA.DIFF.DIFFERENT]:
            print('Different directories:')
            for value in diff_dict[SDA.DIFF.DIFFERENT]:
                for key in MijlpaalDirectory.DIFF:
                    if entry := value.get(key,None):
                        print(entry)
                        match key:
                            case MijlpaalDirectory.DIFF.DIRECTORY:
                                print(f'directory names: {File.display_file(value)} (check, should be implausible)')
                            case MijlpaalDirectory.DIFF.FILES:
                                self._print_file_diff(stored, entry.get(Files.DIFF.EXTRA, None), 'Extra files:')
                                self._print_file_diff(stored, entry.get(Files.DIFF.MISSING, None), 'Missing files:')
                                self._print_file_diff(stored, entry.get(Files.DIFF.DIFFERENT, None), 'Different files:')

    def _print_diff(self, stored: StudentDirectory, difference:dict):
        for key,value in difference.items():
            match key:
                case StudentDirectory.DIFF.STUDENT: print(f'student: {stored.student} - {value}')
                case StudentDirectory.DIFF.DIRECTORY: print(f'dir: {File.display_file(stored.directory)} - {File.display_file(value)}')
                case StudentDirectory.DIFF.BASEDIR: print(f'basedir: {stored.base_dir} - {value}')
                case StudentDirectory.DIFF.STATUS: print(f'status: {stored.status} - {value}')
                case StudentDirectory.DIFF.DIRS: 
                    print(f'DIRS:')
                    self._print_dir_diff(stored, value)                                                     
                case _:print(f'He? {key} {value}')


    def compare_with_database(self, actual_student_directory: StudentDirectory):
        stored = self.stud_dir_queries.find_student_dir_for_directory(actual_student_directory.student, actual_student_directory.directory)
        difference = stored.difference(actual_student_directory)
        self._print_diff(stored, difference)
    def sync_student_dir(self, directory: str, preview=False)->bool:
        log_info(f'\t{File.display_file(directory)}:', to_console=True)
        actual_student_dir = self.detector.process(directory,self.storage,True)
        self.compare_with_database(actual_student_dir)
        # print(actual_student_dir)

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
