from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.undo_logs import UndoLog
from data.classes.base_dirs import BaseDir
from data.classes.milestones import Milestone, StudentMilestones
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.studenten import StudentQueries
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string, test_directory_exists
from general.config import ListValueConvertor, config
from general.log import log_error, log_info, log_print, log_warning
from general.singular_or_plural import sop
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline
from process.scan.importing.dirname_parser import DirectoryNameParser

def init_config():
    config.register('detect_directory', 'skip', ListValueConvertor)
    config.init('detect_directory', 'skip', ['01 Formulieren', 'aapa', 'Beoordeling aanvragen 2023'])    
init_config()

class DetectorException(Exception): pass

class StudentMilestonesDetector(FileProcessor):
    ERRCOMMENT= 'Directory kan niet worden herkend'
    def __init__(self):
        super().__init__(description='StudentMilestone Detector')
        self.parser = DirectoryNameParser()
        self.base_dir: BaseDir = None
        self.current_student_milestones: StudentMilestones = None
    
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
        if max_id := storage.find_max_value('aanvragen', attribute='id', where_attributes='stud_id', where_values=student.id):
            return storage.read('aanvragen', max_id)
    def _get_basedir(self, dirname: str, storage: AAPAStorage)->BaseDir:
        if stored:=storage.find_values('basedirs', attributes='dirname', values=str(Path(dirname).parent)):
            if len(stored) > 1:
                raise DetectorException(f'More than one basedir with same name in database:\n{[str(basedir) for basedir in stored]}')
            self.base_dir = stored[0]
            return True
        self.base_dir = None
        return False   
    def _process_subdirectory(self, subdirectory: str, student: Student)->Milestone:
        if not (parsed := self.parser.parsed(subdirectory)):
            log_warning(f'Onverwachte directory ({Path(subdirectory).stem})')
            return None
        match parsed.type.lower():
            case 'pva' | 'plan van aanpak': verslag_type = Verslag.Type.PVA
            case 'onderzoeksverslag': verslag_type = Verslag.Type.ONDERZOEKS_VERSLAG
            case 'technisch verslag': verslag_type = Verslag.Type.TECHNISCH_VERSLAG
            case 'eindverslag': verslag_type = Verslag.Type.EIND_VERSLAG
            case _: 
                log_warning(f'Soort verslag "{parsed.type}" niet herkend.')
                return None
        return Verslag(verslag_type=verslag_type, student=student, file=None, datum=parsed.datum)
    def report_milestones(self, msg: str, student_milestones: StudentMilestones):
        log_print(msg)
        for student_milestone in student_milestones.milestones:
            log_print(f'\t{student_milestone.summary()}')
    def process_file(self, dirname: str, storage: AAPAStorage = None, preview=False, do_it=False)->StudentMilestones:
        if not test_directory_exists(dirname):
            log_error(f'Directory {dirname} niet gevonden.')
            return None
        log_print(f'Verwerken {summary_string(dirname, maxlen=100)}')
        if not self._get_basedir(dirname, storage):
            log_error(f'Onbekende of nieuwe basisdirectory {summary_string(dirname, maxlen=100)}')
            return None
        try:    
            student = self._get_student(dirname, storage)  
            log_print(f'Student: {student}')
            student_milestones = StudentMilestones(student, self.base_dir)
            if do_it and (aanvraag := self._get_aanvraag(student, storage)):
                student_milestones.add(aanvraag)
            for subdirectory in Path(dirname).glob('*'):
                if subdirectory.is_dir() and (new_milestone:= self._process_subdirectory(subdirectory, student)):                    
                    student_milestones.add(new_milestone)
            self.report_milestones('Gedetecteerd:', student_milestones)
            return student_milestones
        except DetectorException as reader_exception:
            log_warning(f'{reader_exception}\n\t{StudentMilestonesDetector.ERRCOMMENT}.')
        return None
    
class MilestoneDetectorPipeline(FilePipeline):
    def __init__(self, description: str, storage: AAPAStorage, skip_directories:list[str]=[]):
        super().__init__(description, StudentMilestonesDetector(), storage, activity=UndoLog.Action.DETECT)
        self.skip_directories=skip_directories
    def _store_new(self, milestones: StudentMilestones):
        # for aanvraag in milestones.get(Verslag.Type.AANVRAAG):
        #     if not storage.aanvragen
        #  self.storage.aanvragen.create(aanvraag)
        # self.log_aanvraag(aanvraag)   
        # log_print(f'\tstoring new milestone: {milestone}')
        pass
    def _skip(self, filename: str)->bool:        
        if Path(filename).stem in self.skip_directories:
            return True
        return False

def detect_from_directory(directory: str, storage: AAPAStorage, preview=False, do_it=True)->int:
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start import van map  {directory}...', to_console=True)
    importer = MilestoneDetectorPipeline(f'Detectie studentaanvragen uit directory {directory}', storage, skip_directories=config.get('detect_directory', 'skip'))
    # first_id = storage.aanvragen.max_id() + 1
    (n_processed, n_files) = importer.process([dir for dir in Path(directory).glob('*') if (dir.is_dir() and str(dir).find('.git') ==-1)], preview=preview, do_it=do_it)
    # report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    # log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(n_processed, "nieuwe student-mijlpaal", "nieuwe student-mijlpalen")}. In directory: {sop(n_files, "directory", "directories")})', to_console=True)
    return n_processed, n_files      