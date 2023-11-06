from pathlib import Path
from data.classes.action_log import ActionLog
from data.classes.milestones import StudentMilestone, StudentMilestones
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.storage import AAPAStorage
from general.fileutil import summary_string, test_directory_exists
from general.log import log_error, log_info, log_print, log_warning
from general.singular_or_plural import sop
from process.general.base_processor import FileProcessor
from process.general.pipeline import FilePipeline
from process.scan.importing.dirname_parser import DirectoryNameParser

class DetectorException(Exception): pass
class StudentMilestoneDetector(FileProcessor):
    ERRCOMMENT= 'Directory kan niet worden herkend'
    def __init__(self):
        super().__init__(description='StudentMilestone Detector')
        self.parser = DirectoryNameParser()
    def _get_student(self, student_from_directory: str, storage: AAPAStorage):
        words = []
        for word in student_from_directory.split(','):
            words.insert(0,word.strip())
        first_name = words[0]
        full_name = ' '.join(words)
        student = Student(full_name=full_name, first_name=first_name)
        if storage and (stored := storage.studenten.find_student_by_name_or_email(student)):            
            return stored
        return student
    def process_file(self, dirname: str, storage: AAPAStorage = None, preview=False)->Student|StudentMilestone:
        if not test_directory_exists(dirname):
            log_error(f'Directory {dirname} niet gevonden.')
            return None
        log_print(f'Verwerken {summary_string(dirname, maxlen=100)}')
        try:      
            if not (parsed := self.parser.parsed(dirname)):
                return None
            if not (student := self._get_student(parsed.student, storage)):
                log_error(f'Directory niet herkend')
                return None
            if not parsed.type:
                return student
            match parsed.type.lower():
                case 'pva' | 'plan van aanpak': verslag_type = StudentMilestone.Type.PVA
                case 'onderzoeksverslag': verslag_type = StudentMilestone.Type.ONDERZOEKS_VERSLAG
                case 'technisch verslag': verslag_type = StudentMilestone.Type.TECHNISCH_VERSLAG
                case 'eindverslag': verslag_type = StudentMilestone.Type.EIND_VERSLAG
                case _: 
                    log_error(f'Soort verslag "{parsed.type}" niet herkend.')
                    return None
            return Verslag(verslag_type=verslag_type, student = student, file=None, datum=parsed.datum)
        except DetectorException as reader_exception:
            log_warning(f'{reader_exception}\n\t{StudentMilestoneDetector.ERRCOMMENT}.')
        return None
    
class MilestoneDetectorPipeline(FilePipeline):
    def __init__(self, description: str, storage: AAPAStorage):
        super().__init__(description, StudentMilestoneDetector(), storage, activity=ActionLog.Action.DETECT)
    def _store_new(self, milestone: StudentMilestone):
        # self.storage.aanvragen.create(aanvraag)
        # self.log_aanvraag(aanvraag)   
        log_print(f'\tnew milestone: {milestone}')
        pass

def detect_from_directory(directory: str, storage: AAPAStorage, preview=False)->int:
    if not Path(directory).is_dir():
        log_error(f'Map {directory} bestaat niet. Afbreken.')
        return 0  
    log_info(f'Start import van map  {directory}...', to_console=True)
    importer = MilestoneDetectorPipeline(f'Detectie studentaanvragen uit directory {directory}', storage)
    # first_id = storage.aanvragen.max_id() + 1
    (n_processed, n_files) = importer.process([dir for dir in Path(directory).rglob('*') if (dir.is_dir() and str(dir).find('.git') ==-1)], preview)
    # report_imports(importer.storage.aanvragen.read_all(lambda a: a.id >= first_id), preview=preview)
    # log_debug(f'NOW WE HAVE: {n_processed=} {n_files=}')
    log_info(f'...Import afgerond ({sop(n_processed, "nieuwe student-mijlpaal", "nieuwe student-mijlpalen")}. In directory: {sop(n_files, "directory", "directories")})', to_console=True)
    return n_processed, n_files      