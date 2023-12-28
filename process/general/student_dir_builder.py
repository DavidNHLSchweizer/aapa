import datetime
from pathlib import Path
from data.classes.base_dirs import BaseDir
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.storage.aapa_storage import AAPAStorage
from data.storage.general.storage_const import StorageException
from data.storage.queries.base_dirs import BaseDirQueries
from data.storage.queries.student_directories import StudentDirectoryQueries
from data.storage.queries.studenten import StudentQueries
from general.log import log_warning

class StudentDirectoryBuilder:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
    def _create_new_student_directory(self, student: Student, filename: str)->StudentDirectory:
        directory = Path(filename).parent
        basedir_queries : BaseDirQueries = self.storage.queries('base_dirs')
        if not (base_dir := basedir_queries.find_basedir(directory)):
            raise StorageException(f'Kan student directory voor {student} bestand {filename} niet aan basis-directory koppelen.\nBasis-directory moet eerst worden aangemaakt.')
        stud_dir_name = base_dir.get_student_directory(student)
        if not directory.is_relative_to(Path(stud_dir_name)):
            raise StorageException(f'Bestand {filename} staat niet op de verwachte plaats.\n\tVerwacht wordt (sub)directory {stud_dir_name}.')
        return StudentDirectory(student, stud_dir_name, base_dir)
    @staticmethod
    def get_student_dir_name(storage: AAPAStorage, student: Student, output_directory: str):
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
    def __get_stud_dir(self, student: Student, filename: str):
        queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        if not (stud_dir := queries.find_student_dir(student)):
            stud_dir = self._create_new_student_directory(student, filename)
            self.storage.create('student_directories', stud_dir)
        return stud_dir
    def __get_mijlpaal_directory(self, stud_dir: StudentDirectory, directory: str, datum: datetime.datetime, mijlpaal_type)->MijlpaalDirectory:
        if not (mp_dir := stud_dir.get_directory(datum, mijlpaal_type)):
            mp_dir = MijlpaalDirectory(mijlpaal_type, directory, datum)
            stud_dir.add(mp_dir)
        if mp_dir.directory != directory:
            raise StorageException(f'Onverwachte directory {directory}. Inconsistente of corrupte database.')
        return mp_dir
    def register_file(self, student: Student, datum: datetime.datetime, filename: str, filetype: File.Type, mijlpaal_type: MijlpaalType):
        self.storage.ensure_key('studenten', student)        
        stud_dir = self.__get_stud_dir(student, filename)
        mp_dir = self.__get_mijlpaal_directory(stud_dir, str(Path(filename).parent), datum, mijlpaal_type)
        mp_dir.register_file(filename,filetype,mijlpaal_type)
        self.storage.update('student_directories', stud_dir)
    def register_basedir(self, year: int, period: str, forms_version: str, directory: str):
        if not self.storage.find_values('base_dirs', [year, period], [year,period]):
            self.storage.create('base_dirs', BaseDir(year, period, forms_version, directory))
        
