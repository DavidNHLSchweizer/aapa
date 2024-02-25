""" CORRECT_MP_DIRS. 

    aanpassen van database voor dubbelingen in mijlpaal_directories voor aanvragen.

    Gerelateerde bug (gefixt in programma 1.34):
    Nieuwe aanvragen worden in een nieuwe mijlpaal_directory gezet, ook als deze in de 
    bestaande mijlpaal_directory hoorden.
    
    bedoeld voor migratie db naar versie 1.23
    
"""
from pathlib import Path
from data.classes.files import File
from data.general.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.general.roots import Roots
from storage.queries.student_directories import StudentDirectoriesQueries
from main.log import log_warning
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class MijlpaalDirsReEngineeringProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('student_directory_directories', SQLcollector({'delete': {'sql': 'delete from STUDENT_DIRECTORY_DIRECTORIES where mp_dir_id in (?)'},}))
        sql.add('mijlpaal_directory_files', SQLcollector({'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES(mp_dir_id,file_id) values(?,?)'},
                                                               'delete': {'sql': 'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id in (?)'},}))
        sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,kans=?,directory=?,datum=? where id=?'},
                                                           'delete': {'sql': 'delete from MIJLPAAL_DIRECTORIES where id in (?)'},}))
        return sql
    def _sql_delete_mijlpaal_directory_files(self, mp_dir: MijlpaalDirectory):
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
    def _sql_delete_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self._sql_delete_mijlpaal_directory_files(mp_dir)
        self.sql.delete('student_directory_directories', [mp_dir.id])
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
    def _sql_update_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
        self.sql.update('mijlpaal_directories', [mp_dir.mijlpaal_type,mp_dir.kans,
                                                 Roots.encode_path (mp_dir.directory), TSC.timestamp_to_sortable_str(mp_dir.datum), mp_dir.id])
    def process_student(self, student: Student):      
        student_directory = self.student_dir_queries.find_student_dir(student)
        listing = {}
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        listing[student.full_name] = student_directory.get_directories(mijlpaal_type=MijlpaalType.AANVRAAG, sorted=False)
        
    def _check_doublures(self, dir_list: list[MijlpaalDirectory])-> list[MijlpaalDirectory]:
        must_remove=[]
        prv_dir = None
        cur_cnt = 0
        for mp_dir in dir_list:
            if not prv_dir or prv_dir.directory != mp_dir.directory:
                if cur_cnt == 1:
                    must_remove.append(prv_dir)
                prv_dir = mp_dir
                cur_cnt = 1
            else:
                cur_cnt += 1
        return [mp_dir for mp_dir in dir_list if mp_dir not in must_remove]      
    def get_student_dirs(self, student_directory: StudentDirectory)->list[MijlpaalDirectory]:
        dirs = self._check_doublures(student_directory.get_directories(mijlpaal_type=MijlpaalType.AANVRAAG, sorted=False))
        if dirs and len(dirs) > 1:
            return sorted(dirs, key=lambda d: d.id)
        else:
            return None
    def _get_all_directories(self)->dict:
        listing = {}
        for student in sorted(filter(lambda s: s.status in Student.Status.active_states(), self.storage.queries('studenten').find_all()),
                              key = lambda s: s.full_name):
            student_directory = self.student_dir_queries.find_student_dir(student)
            if not student_directory:
                log_warning(f'Geen directory gevonden voor student {student}.')
                continue
            if (dirlist := self.get_student_dirs(student_directory)):
                listing[student.email] = {'student': student, 'stud_dir': student_directory, 'dirs': dirlist}
        return listing
    def _correct_directory(self, mp_dir_list: list[MijlpaalDirectory]):
        datum = None
        for mp_dir in mp_dir_list:
            if mp_dir.datum != 0:
                datum = mp_dir.datum
                break
        first_mp_dir = mp_dir_list[0] # the list was sorted on id`
        first_mp_dir.datum = datum
        self._sql_delete_mijlpaal_directory_files(first_mp_dir)
        for mp_dir in mp_dir_list[1:]:
            for file in mp_dir.files.files:
                first_mp_dir.files.add(file)
            self._sql_delete_mijlpaal_directory(mp_dir)
            mp_dir.files.clear('files')
        self._sql_update_mijlpaal_directory(first_mp_dir)
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        def dump_info(msg: str, dir_list:list[MijlpaalDirectory]):
            self.log(f'\t--- {msg} ---')
            for dir in dir_list:
                filestr = "\n\t\t".join([Path(file.filename).name for file in dir.files_list]) if dir.files_list else '<No files>'
                self.log(f'\t{dir.id}-{dir.datum}: {File.display_file(dir.directory)}\n\t\t{filestr}')
        for entry in self._get_all_directories().values():
            self.log(f'{entry["student"]}:')
            stud_dir: StudentDirectory = entry['stud_dir']
            self.log(f'\tStudent Directory ({stud_dir.id}): {File.display_file(stud_dir.directory)} ({stud_dir.status}).')
            dump_info('before', entry['dirs'])
            self._correct_directory(entry['dirs'])
            dump_info('after', entry['dirs'])
        return True
