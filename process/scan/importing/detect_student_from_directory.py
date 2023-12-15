from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directory import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.undo_logs import UndoLog
from data.classes.base_dirs import BaseDir
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.roots import decode_path
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.base_dirs import BaseDirQueries
from data.storage.queries.studenten import StudentQueries
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string, test_directory_exists
from general.config import ListValueConvertor, config
from general.log import log_debug, log_error, log_info, log_print, log_warning
from general.singular_or_plural import sop
from general.timeutil import TSC
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline
from process.scan.importing.dirname_parser import DirectoryNameParser
from process.scan.importing.filename_parser import FileTypeDetector

def init_config():
    config.register('detect_directory', 'skip', ListValueConvertor)
    config.init('detect_directory', 'skip', ['01 Formulieren', 'aapa', 'Beoordeling aanvragen 2023'])    
init_config()

class DetectorException(Exception): pass

class StudentDirectoryDetector(FileProcessor):
    ERRCOMMENT= 'Directory kan niet worden herkend'
    def __init__(self):
        super().__init__(description='StudentDirectory Detector')
        self.parser = DirectoryNameParser()
        self.filetype_detector = FileTypeDetector()
        self.base_dir: BaseDir = None
        self.current_student_directory: StudentDirectory = None
    
    def _get_student(self, student_directory: str, storage: AAPAStorage):
        if not (parsed := self.parser.parsed(student_directory)):
            raise DetectorException(f'directory {student_directory} kan niet worden herkend.')
        student = Student(full_name=parsed.student)
        queries: StudentQueries = storage.queries('studenten')
        if storage and (stored := queries.find_student_by_name_or_email(student)):
            return stored
        return student
    def _get_aanvraag(self, student: Student, storage: AAPAStorage)->Aanvraag:
        if student.id == EMPTY_ID:
            return None
        if max_id := storage.find_max_value('aanvragen', attribute='id', where_attributes='student', where_values=student.id):
            return storage.read('aanvragen', max_id)
    def _get_basedir(self, dirname: str, storage: AAPAStorage)->BaseDir:
        queries : BaseDirQueries = storage.queries('base_dirs')
        self.base_dir = queries.find_basedir(dirname)
        return self.base_dir != None
    def _parse_type(self, subdirectory:str, parsed_type: str)->MijlpaalType:
        match parsed_type.lower():
            case 'pva' | 'plan van aanpak': return MijlpaalType.PVA
            case 'onderzoeksverslag': return MijlpaalType.ONDERZOEKS_VERSLAG
            case 'technisch verslag': return MijlpaalType.TECHNISCH_VERSLAG
            case 'eindverslag': return MijlpaalType.EIND_VERSLAG
            case 'product' | 'productbeoordeling': return MijlpaalType.PRODUCT_BEOORDELING
            case 'afstudeerzitting': return MijlpaalType.EINDBEOORDELING
            case _:                 
                if parsed_type:
                    if type_str := self.parser.parse_non_standard(subdirectory, parsed_type):
                        return self._parse_type(subdirectory, type_str)
                    else:
                        log_warning(f'Soort directory "{parsed_type}" niet herkend.')
                else:
                    log_warning(f'Directory {Path(subdirectory).name} niet herkend.')
        return None
    def _collect_files(self, new_dir: MijlpaalDirectory):
        for filename in Path(new_dir.directory).glob('*'):
            if not filename.is_file():
                continue
            log_debug(f'collecting {filename}')
            filetype,mijlpaal_type = self.filetype_detector.detect(filename)
            if filetype == File.Type.UNKNOWN:
                mijlpaal_type = new_dir.mijlpaal_type
                filetype = mijlpaal_type.default_filetype()
            new_dir.register_file(filename=filename, filetype=filetype, mijlpaal_type=mijlpaal_type)
    def _process_subdirectory(self, subdirectory: str, student: Student)->MijlpaalDirectory:
        if not (parsed := self.parser.parsed(subdirectory)):
            log_warning(f'Onverwachte directory ({Path(subdirectory).stem})')
            return None
        if not (mijlpaal_type := self._parse_type(subdirectory, parsed.type)):
            log_error('\tDirectory wordt overgeslagen. Kan niet worden herkend.')
            return None
        new_dir = MijlpaalDirectory(mijlpaal_type=mijlpaal_type, directory=subdirectory, datum=parsed.datum)
        # log_print(f'\tGedetecteerd: {new_dir}')
        self._collect_files(new_dir)
        return new_dir
    def __update_kansen(self, student_directory: StudentDirectory):
        cur_type = MijlpaalType.UNKNOWN
        cur_kans = 1
        for mijlpaal_directory in sorted(student_directory.directories, key=lambda v: (v.mijlpaal_type, v.datum)):
            if mijlpaal_directory.mijlpaal_type == cur_type:
                cur_kans += 1
            else:
                cur_kans = 1
                cur_type = mijlpaal_directory.mijlpaal_type
            mijlpaal_directory.kans = cur_kans
    def report_directory(self, msg: str, student_directory: StudentDirectory):
        log_print(msg)
        for directory in student_directory.directories:
            log_print(f'\t{directory.summary()}')
    def process_file(self, dirname: str, storage: AAPAStorage = None, preview=False)->StudentDirectory:
        if not test_directory_exists(dirname):
            log_error(f'Directory {dirname} niet gevonden.')
            return None
        log_print(f'Verwerken {summary_string(dirname, maxlen=100)}')
        if not self._get_basedir(dirname, storage):
            log_error(f'Directory {summary_string(dirname, maxlen=100)} kan niet worden gelinkt met bekende basisdirectory.')
            return None
        try:    
            student = self._get_student(dirname, storage)  
            log_print(f'Student: {student}')
            if not student.valid():
                log_warning(f'Gegevens student {student} zijn niet compleet.')
            student_directory = StudentDirectory(student, dirname, self.base_dir)
            new_dir = MijlpaalDirectory(mijlpaal_type=MijlpaalType.AANVRAAG, directory=dirname, datum=TSC.AUTOTIMESTAMP)
            self._collect_files(new_dir)
            if new_dir.files.nr_files() > 0:
                student_directory.add(new_dir)
            # if (aanvraag := self._get_aanvraag(student, storage)):
            #     student_directory.add(aanvraag)
            for subdirectory in Path(dirname).glob('*'):
                if subdirectory.is_dir() and (new_item := self._process_subdirectory(subdirectory, student)):                    
                    student_directory.add(new_item)
            self.__update_kansen(student_directory)
            self.report_directory('Student directory:', student_directory)
            return student_directory
        except DetectorException as reader_exception:
            log_warning(f'{reader_exception}\n\t{StudentDirectoryDetector.ERRCOMMENT}.')
        return None
    
class MilestoneDetectorPipeline(FilePipeline):
    def __init__(self, description: str, storage: AAPAStorage, skip_directories:list[str]=[]):
        super().__init__(description, StudentDirectoryDetector(), storage, activity=UndoLog.Action.DETECT)
        self.skip_directories=skip_directories
    def _store_new(self, student_directory: StudentDirectory):
        self.storage.create('student_directories', student_directory)

        # for aanvraag in milestones.get(Verslag.Type.AANVRAAG):
        #     if not storage.aanvragen
        #  self.storage.aanvragen.create(aanvraag)
        # self.log_aanvraag(aanvraag)   
        # log_print(f'\tstoring new milestone: {milestone}')

    def _skip(self, filename: str)->bool:        
        if Path(filename).stem in self.skip_directories:
            return True
        return False

def detect_from_directory(directory: str, storage: AAPAStorage, preview=False, do_it=True)->int:
    directory = decode_path(directory)
    print(directory)
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start detectie van map  {directory}...', to_console=True)
    importer = MilestoneDetectorPipeline(f'Detectie studentgegevens uit directory {directory}', storage, skip_directories=config.get('detect_directory', 'skip'))
    # first_id = storage.aanvragen.max_id() + 1
    (n_processed, n_files) = importer.process([dir for dir in Path(directory).glob('*') if (dir.is_dir() and str(dir).find('.git') ==-1)], preview=preview)
    # report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    # log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Detectie afgerond ({sop(n_processed, "directory", "directories", prefix="nieuwe student-")}. In directory: {sop(n_files, "subdirectory", "subdirectories")})', to_console=True)
    return n_processed, n_files      