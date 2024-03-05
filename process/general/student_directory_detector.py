from pathlib import Path
from data.classes.files import File
from data.classes.base_dirs import BaseDir
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.general.const import MijlpaalType
from general.fileutil import test_directory_exists
from general.timeutil import TSC
from main.log import log_debug, log_error, log_info, log_print, log_warning
from process.input.importing.dirname_parser import DirectoryNameParser
from process.input.importing.filename_parser import FileTypeDetector
from storage.aapa_storage import AAPAStorage
from storage.queries.base_dirs import BaseDirsQueries
from storage.queries.studenten import StudentenQueries

class StudentDirectoryDetectorException(Exception): pass
class StudentDirectoryDetector:
    ERRCOMMENT= 'Directory kan niet worden herkend'
    def __init__(self, verbose=False):
        self.parser = DirectoryNameParser()
        self.filetype_detector = FileTypeDetector()
        self.base_dir: BaseDir = None
        self.current_student_directory: StudentDirectory = None
        self.new_students:dict[int:Student] = {}   
        self.verbose = verbose
    def _get_basedir(self, dirname: str, storage: AAPAStorage)->BaseDir:
        queries : BaseDirsQueries = storage.queries('base_dirs')
        self.base_dir = queries.find_basedir(dirname)
        return self.base_dir != None
    def _get_student(self, student_directory: str, storage: AAPAStorage)->Student:
        if not (parsed := self.parser.parsed(student_directory)):
            raise StudentDirectoryDetectorException(f'directory {File.display_file(student_directory)} kan niet worden herkend.')
        student = Student(full_name=parsed.student,email=parsed.email())
        queries: StudentenQueries = storage.queries('studenten')
        if storage and (stored := queries.find_student_by_name_or_email_or_studnr(student)):
            return stored
        storage.ensure_key('studenten',student)
        self.new_students[student.id] = student
        return student
    def _parse_type(self, subdirectory:str, parsed_type: str)->MijlpaalType:
        match parsed_type.lower():
            case 'pva' | 'plan van aanpak': return MijlpaalType.PVA
            case 'onderzoeksverslag'|'onderzoek': return MijlpaalType.ONDERZOEKS_VERSLAG
            case 'technisch verslag': return MijlpaalType.TECHNISCH_VERSLAG
            case 'eindverslag': return MijlpaalType.EIND_VERSLAG
            case 'product' | 'productbeoordeling': return MijlpaalType.PRODUCT_BEOORDELING
            case 'afstudeerzitting' | 'zitting afstuderen': return MijlpaalType.EINDBEOORDELING
            case _:                 
                if parsed_type:
                    if type_str := self.parser.parse_non_standard(subdirectory, parsed_type):
                        return self._parse_type(subdirectory, type_str)
                    else:
                        log_warning(f'Soort directory "{parsed_type}" niet herkend.')
                else:
                    log_warning(f'Directory {File.display_file(Path(subdirectory).name)} niet herkend.')
        return None
    def _collect_files(self, new_dir: MijlpaalDirectory):
        for filename in Path(new_dir.directory).glob('*'):
            if not filename.is_file():
                continue
            log_debug(f'collecting {filename}')
            filetype,mijlpaal_type = self.filetype_detector.detect(filename)
            if filetype == File.Type.UNKNOWN:
                mijlpaal_type = new_dir.mijlpaal_type
                if mijlpaal_type == MijlpaalType.AANVRAAG:
                    if Path(filename).suffix == '.pdf':
                        filetype = File.Type.AANVRAAG_PDF
                    else:
                        filetype = File.Type.AANVRAAG_OTHER 
                else:
                    filetype = mijlpaal_type.default_filetype()
            log_debug(f'collected: {filetype} {mijlpaal_type}')
            new_dir.register_file(filename=filename, filetype=filetype, mijlpaal_type=mijlpaal_type)
            log_debug('registered')
    def _process_subdirectory(self, subdirectory: str, student: Student)->MijlpaalDirectory:
        if not (parsed := self.parser.parsed(subdirectory)):
            log_warning(f'Onverwachte directory ({Path(subdirectory).stem})')
            return None
        if not (mijlpaal_type := self._parse_type(subdirectory, parsed.type)):
            log_error(f'\tDirectory {File.display_file(subdirectory)} wordt overgeslagen. Kan niet worden herkend.')
            return None
        new_dir = MijlpaalDirectory(mijlpaal_type=mijlpaal_type, directory=subdirectory, datum=parsed.datum)
        log_debug(f'\tGedetecteerd: {new_dir}')
        self._collect_files(new_dir)
        log_debug('ready detecting')
        return new_dir
    def __ensure_keys(self, student_directory: StudentDirectory, storage: AAPAStorage):
        storage.ensure_key('student_directories', student_directory)
        for mp_dir in student_directory.directories:
            storage.ensure_key('mijlpaal_directories', mp_dir)
            for file in mp_dir.files_list:
                storage.ensure_key('files', file)
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
        self.log(msg)
        for directory in student_directory.directories:
            self.log(f'\t{str(directory)}')
    def log(self, message: str):
        if self.verbose:
            log_print(message)
        else:
            log_info(message)
    def is_new_student(self, student: Student)->bool:
        return student in self.new_students.values()
    def process(self, dirname: str, storage: AAPAStorage = None, preview=False)->StudentDirectory:
        if not test_directory_exists(dirname):
            log_error(f'Directory {dirname} niet gevonden.')
            return None
        log_info(f'Inlezen vanaf directory {File.display_file(dirname)}')
        if not self._get_basedir(dirname, storage):
            log_error(f'Directory {File.display_file(dirname)} kan niet worden gelinkt met bekende basisdirectory.')
            return None
        try:    
            student = self._get_student(dirname, storage)
            log_print(f'Student: {student}')
            if self.is_new_student(student):
                log_warning(f'Student {student} nog niet in database. Wordt toegevoegd.\n\tLET OP: controleer het berekende email-adres {student.email} en voeg het juiste studentnummer toe.')
            elif not student.valid():
                log_warning(f'Gegevens student {student} zijn niet compleet.')
            student_directory = StudentDirectory(student, dirname, self.base_dir)
            new_dir = MijlpaalDirectory(mijlpaal_type=MijlpaalType.AANVRAAG, directory=dirname, datum=TSC.AUTOTIMESTAMP)
            self._collect_files(new_dir)
            if new_dir.nr_items() > 0:
                student_directory.add(new_dir)
            for subdirectory in Path(dirname).glob('*'):
                if subdirectory.is_dir() and (new_item := self._process_subdirectory(subdirectory, student)):                    
                    student_directory.add(new_item)
            self.__ensure_keys(student_directory,storage)
            self.__update_kansen(student_directory)
            self.report_directory('Student directory:', student_directory)
            return student_directory
        except StudentDirectoryDetectorException as reader_exception:
            log_warning(f'{reader_exception}\n\t{StudentDirectoryDetector.ERRCOMMENT}.')
        return None
