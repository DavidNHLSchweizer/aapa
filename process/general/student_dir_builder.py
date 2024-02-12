import datetime
from pathlib import Path
from typing import Tuple
from data.classes.base_dirs import BaseDir
from data.general.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from storage.aapa_storage import AAPAStorage
from storage.general.storage_const import StorageException
from storage.queries.base_dirs import BaseDirQueries
from storage.queries.student_directories import StudentDirectoryQueries
from storage.queries.studenten import StudentQueries
from general.fileutil import last_parts_file
from main.log import log_error, log_print, log_warning

class StudentDirectoryBuilder:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
    def _register_new_student_directory(self, student: Student, filename: str)->StudentDirectory:
        directory = Path(filename).parent
        basedir_queries : BaseDirQueries = self.storage.queries('base_dirs')
        if not (base_dir := basedir_queries.find_basedir(directory)):
            raise StorageException(f'Kan student directory voor {student} bestand {filename} niet aan basis-directory koppelen.\nBasis-directory moet eerst worden aangemaakt.')
        stud_dir_name = base_dir.get_student_directory(student)
        if not directory.is_relative_to(Path(stud_dir_name)):
            raise StorageException(f'Bestand {filename} staat niet op de verwachte plaats.\n\tVerwacht wordt (sub)directory {stud_dir_name}.')
        return StudentDirectory(student, stud_dir_name, base_dir, StudentDirectory.Status.ACTIVE)
    @staticmethod
    def get_student_dir_name(storage: AAPAStorage, student: Student, output_directory: str)->str:
        student_queries: StudentQueries = storage.queries('studenten')
        if (stored:=student_queries.find_student_by_name_or_email_or_studnr(student)):
            student = stored
        student_dir_queries: StudentDirectoryQueries= storage.queries('student_directories')       
        if (student_dir := student_dir_queries.find_student_dir(student)):
            return student_dir.directory
        else:
            basedir_queries : BaseDirQueries = storage.queries('base_dirs')
            if not (base_dir := basedir_queries.find_basedir(output_directory, start_at_parent = False)):
                if not (base_dir := basedir_queries.last_base_dir()):
                    raise StorageException(f'Geen basis-directories gedefinieerd.')
            return base_dir.get_student_directory(student)
    @staticmethod
    def get_mijlpaal_directory_name(stud_dir: StudentDirectory, datum: datetime.datetime, mijlpaal_type: MijlpaalType)->str:
        return str(Path(stud_dir.directory).joinpath(MijlpaalDirectory.directory_name(mijlpaal_type, datum)))
    def __check_must_register_new_student_directory(self, student: Student, target_basedir: BaseDir, filename: str)->Tuple[bool, StudentDirectory]:
        queries: StudentDirectoryQueries = self.storage.queries('student_directories')        
        if not (stud_dir := queries.find_student_dir(student)):
            return (True,None)
        elif stud_dir.base_dir != target_basedir:
            log_warning(f'Bestand {last_parts_file(filename)}\n\tstaat niet in bekende directory voor student: {last_parts_file(stud_dir.directory)}.')
            stud_dir.status = StudentDirectory.Status.ARCHIVED
            self.storage.update('student_directories', stud_dir)
            return (True,None)
        return (False,stud_dir)
    def __get_stud_dir(self, student: Student, filename: str)->StudentDirectory:        
        basedir_queries: BaseDirQueries = self.storage.queries('base_dirs')
        if not (basedir_from_file := basedir_queries.find_basedir(Path(filename).parent)):
            log_error(f'Basisdirectory voor toe te voegen bestand kan niet worden gevonden.\n\tBestand {filename}\n\tkan niet worden geregistreerd.')
            return None
        (must_create,stud_dir) = self.__check_must_register_new_student_directory(student, basedir_from_file, filename)
        if must_create:
            stud_dir = self._register_new_student_directory(student, filename)
            log_print(f'Nieuwe directory voor student wordt geregistreerd: {stud_dir.directory}.')
            self.storage.create('student_directories', stud_dir)
        return stud_dir
    def __get_mijlpaal_directory(self, stud_dir: StudentDirectory, directory: str, datum: datetime.datetime, mijlpaal_type)->MijlpaalDirectory:
        if not (mp_dir := stud_dir.get_directory(datum, mijlpaal_type)):
            mp_dir = MijlpaalDirectory(mijlpaal_type, directory, datum)
            stud_dir.add(mp_dir)
        if mp_dir.directory != directory: 
            log_warning(f'Bestand staat op onverwachte plek ({directory}).\n\tAndere bestanden voor deze student staan in directory is {mp_dir.directory}.\n\tIndien dit bewust zo gedaan is kan deze waarschuwing genegeerd worden.\n\tAnders: verplaats het document naar de juiste locatie.')
        return mp_dir
    def register_file(self, student: Student, datum: datetime.datetime, filename: str, 
                      filetype: File.Type, mijlpaal_type: MijlpaalType)->Tuple[StudentDirectory, MijlpaalDirectory]:
        self.storage.ensure_key('studenten', student)        
        if not (stud_dir := self.__get_stud_dir(student, filename)):
            raise StorageException(f'Kan studentdirectory niet vinden of aanmaken. \nStudent: {student.full_name} Filename: {filename}')       
        mp_dir = self.__get_mijlpaal_directory(stud_dir, str(Path(filename).parent), datum, mijlpaal_type)
        mp_dir.register_file(filename,filetype,mijlpaal_type)
        self.storage.update('student_directories', stud_dir)
        return (stud_dir,mp_dir)
    def register_basedir(self, year: int, period: str, forms_version: str, directory: str):
        if not self.storage.find_values('base_dirs', [year, period], [year,period]):
            self.storage.create('base_dirs', BaseDir(year, period, forms_version, directory))
        