import datetime
from pathlib import Path
from typing import Tuple
from data.classes.aanvragen import Aanvraag
from data.classes.base_dirs import BaseDir
from data.classes.mijlpaal_base import MijlpaalGradeable
from data.classes.verslagen import Verslag
from data.general.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from general.obsolete import obsolete_exception
from general.timeutil import TSC
from main.config import FloatValueConvertor, config
from storage.aapa_storage import AAPAStorage
from storage.general.storage_const import StorageException
from storage.queries.base_dirs import BaseDirsQueries
from storage.queries.student_directories import StudentDirectoriesQueries
from storage.queries.studenten import StudentenQueries
from main.log import log_error, log_print, log_warning

def init_config():
    config.register('directories', 'error_margin_date', FloatValueConvertor)
    config.init('directories', 'error_margin_date', 3.0)
init_config()


class StudentDirectoryBuilder:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
    def _register_new_student_directory(self, student: Student, filename: str)->StudentDirectory:
        directory = Path(filename).parent
        basedir_queries : BaseDirsQueries = self.storage.queries('base_dirs')
        if not (base_dir := basedir_queries.find_basedir(directory)):
            raise StorageException(f'Kan student directory voor {student} bestand {filename} niet aan basis-directory koppelen.\nBasis-directory moet eerst worden aangemaakt.')
        stud_dir_name = base_dir.get_student_directory_name(student)
        if not directory.is_relative_to(Path(stud_dir_name)):
            raise StorageException(f'Bestand {filename} staat niet op de verwachte plaats.\n\tVerwacht wordt (sub)directory {stud_dir_name}.')
        return StudentDirectory(student, stud_dir_name, base_dir, StudentDirectory.Status.ACTIVE)
    @staticmethod
    def get_student_dir(storage: AAPAStorage, student: Student, output_directory: str)->StudentDirectory:
        student_queries: StudentenQueries = storage.queries('studenten')
        if (stored:=student_queries.find_student_by_name_or_email_or_studnr(student)):
            student = stored
        student_dir_queries: StudentDirectoriesQueries= storage.queries('student_directories')       
        if (student_dir := student_dir_queries.find_student_dir(student)):
            return student_dir
        else:
            basedir_queries : BaseDirsQueries = storage.queries('base_dirs')
            if not (base_dir := basedir_queries.find_basedir(output_directory, start_at_parent = False)):
                if not (base_dir := basedir_queries.last_base_dir()):
                    raise StorageException(f'Geen basis-directories gedefinieerd.')
            return StudentDirectory(student,BaseDir.get_directory_name(student), base_dir, status=StudentDirectory.Status.ACTIVE)
    @staticmethod
    def get_student_dir_name(storage: AAPAStorage, student: Student, output_directory: str)->str:
        student_queries: StudentenQueries = storage.queries('studenten')
        if (stored:=student_queries.find_student_by_name_or_email_or_studnr(student)):
            student = stored
        student_dir_queries: StudentDirectoriesQueries= storage.queries('student_directories')       
        if (student_dir := student_dir_queries.find_student_dir(student)):
            return student_dir.directory
        else:
            basedir_queries : BaseDirsQueries = storage.queries('base_dirs')
            if not (base_dir := basedir_queries.find_basedir(output_directory, start_at_parent = False)):
                if not (base_dir := basedir_queries.last_base_dir()):
                    raise StorageException(f'Geen basis-directories gedefinieerd.')
            return base_dir.get_student_directory_name(student)
    @staticmethod
    def get_mijlpaal_directory_name(stud_dir: StudentDirectory, datum: datetime.datetime, mijlpaal_type: MijlpaalType)->str:
        """ geeft de naam van het volledige pad voor mijlpaaldirectory met deze datum/type. """
        return str(Path(stud_dir.directory).joinpath(MijlpaalDirectory.directory_name(mijlpaal_type, datum)))
    def __check_must_register_new_student_directory(self, student: Student, target_basedir: BaseDir, filename: str)->Tuple[bool, StudentDirectory]:
        queries: StudentDirectoriesQueries = self.storage.queries('student_directories')        
        if not (stud_dir := queries.find_student_dir(student)):
            return (True,None)
        elif stud_dir.base_dir != target_basedir:
            log_warning(f'Bestand {File.display_file(filename)}\n\tstaat niet in bekende directory voor student: {File.display_file(stud_dir.directory)}.')
            stud_dir.status = StudentDirectory.Status.ARCHIVED
            self.storage.update('student_directories', stud_dir)
            return (True,None)
        return (False,stud_dir)
    def __get_stud_dir(self, student: Student, filename: str|Path)->StudentDirectory:        
        basedir_queries: BaseDirsQueries = self.storage.queries('base_dirs')
        if not (basedir_from_file := basedir_queries.find_basedir(Path(filename).parent)):
            log_error(f'Basisdirectory voor toe te voegen bestand kan niet worden gevonden.\n\tBestand {filename}\n\tkan niet worden geregistreerd.')
            return None
        (must_create,stud_dir) = self.__check_must_register_new_student_directory(student, basedir_from_file, filename)
        if must_create:
            stud_dir = self._register_new_student_directory(student, filename)
            log_print(f'Nieuwe directory voor student wordt geregistreerd: {File.display_file(stud_dir.directory)}.')
            self.storage.create('student_directories', stud_dir)
        return stud_dir
    def get_mijlpaal_directory(self, stud_dir: StudentDirectory, directory: str, datum: datetime.datetime, 
                                 mijlpaal_type: MijlpaalType, error_margin=0.0)->MijlpaalDirectory:
        if not (mp_dir := stud_dir.get_directory(datum, mijlpaal_type, error_margin=error_margin)):
            kans = len(stud_dir.get_directories(mijlpaal_type))+1
            mp_dir = MijlpaalDirectory(mijlpaal_type=mijlpaal_type, directory=directory, datum=datum, kans = kans)
            self.storage.create('mijlpaal_directories', mp_dir)
            stud_dir.add(mp_dir)
        if str(mp_dir.directory).lower() != str(directory).lower(): 
            log_warning(f'Bestand staat op onverwachte plek ({directory}).\n\tAndere bestanden voor deze student staan in directory {File.display_file(mp_dir.directory)}.\n\tIndien dit bewust zo gedaan is kan deze waarschuwing genegeerd worden.\n\tAnders: verplaats het document naar de juiste locatie.')
        return mp_dir
    def register_file(self, student: Student, datum: datetime.datetime, filename: str, 
                      filetype: File.Type, mijlpaal_type: MijlpaalType)->Tuple[StudentDirectory, MijlpaalDirectory]:
        obsolete_exception('student dir builder register_file')
        # self.storage.ensure_key('studenten', student)        
        # if not (stud_dir := self.__get_stud_dir(student, filename)):
        #     raise StorageException(f'Kan studentdirectory niet vinden of aanmaken. \nStudent: {student.full_name} Filename: {filename}')       
        # error_margin = config.get('directories', 'error_margin_date')
        # mp_dir = self.get_mijlpaal_directory(stud_dir, str(Path(filename).parent), datum, mijlpaal_type, error_margin)
        # if mijlpaal_type != MijlpaalType.AANVRAAG and TSC.round_to_day(mp_dir.datum) != TSC.round_to_day(datum):
        #     log_warning(f'Datum {TSC.get_date_str(datum)} van nieuw bestand is inconsistent met directory\n\t({File.display_file(mp_dir.directory)})')
        # mp_dir.register_file(filename,filetype,mijlpaal_type)
        # self.storage.update('student_directories', stud_dir)
        # return (stud_dir,mp_dir)
    def _register_mijlpaal(self, mijlpaal: MijlpaalGradeable, filename: str = None):
        self.storage.ensure_key(self.storage.module_name(mijlpaal), mijlpaal)
        if not filename:
            filename = mijlpaal.get_base_file()
        if not (stud_dir := self.__get_stud_dir(mijlpaal.student, filename)):
            raise StorageException(f'Kan studentdirectory niet vinden of aanmaken. \nStudent: {mijlpaal.student.full_name} Filename: {File.display_file(filename)}')       
        error_margin = config.get('directories', 'error_margin_date')
        mp_dir = self.get_mijlpaal_directory(stud_dir, str(Path(filename).parent), mijlpaal.datum, mijlpaal.mijlpaal_type
                                             , error_margin)
        self.storage.ensure_key('mijlpaal_directories', mp_dir)
        if mijlpaal.mijlpaal_type != MijlpaalType.AANVRAAG and TSC.round_to_day(mp_dir.datum) != TSC.round_to_day(mijlpaal.datum):
            log_warning(f'Datum {TSC.get_date_str(mijlpaal.datum)} van nieuw bestand is inconsistent met directory\n\t({File.display_file(mp_dir.directory)})')
        mp_dir.register_mijlpaal(mijlpaal)
        self.storage.update('student_directories', stud_dir)
    def register_aanvraag(self, aanvraag: Aanvraag, filename: str = None):
        self._register_mijlpaal(aanvraag, filename)
    def register_verslag(self, verslag: Verslag, filename: str = None):
        self._register_mijlpaal(verslag, filename)
    def _register_file(self, student: Student, file: File)->Tuple[StudentDirectory, MijlpaalDirectory]:
        obsolete_exception('_register_file')
        return self.register_file(student, file.timestamp, file.filename, file.filetype, file.mijlpaal_type)
    # def register_verslag(self, verslag: Verslag):
    #     self.storage.ensure_key('verslagen', verslag)
    #     self.storage.create('verslagen', verslag)
    #     for file in verslag.files_list:
    #         self.register_file(verslag.student, file)            
    def register_basedir(self, year: int, period: str, forms_version: str, directory: str):
        if not self.storage.find_values('base_dirs', [year, period], [year,period]):
            self.storage.create('base_dirs', BaseDir(year, period, forms_version, directory))
SDB=StudentDirectoryBuilder