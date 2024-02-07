""" CORRECT_MP_DIRS. 

    aanpassen van database voor dubbelingen in mijlpaal_directories voor aanvragen.
    bedoeld voor migratie naar versie 1.23
    
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from data.classes.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.roots import Roots
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.student_directories import StudentDirectoryQueries
from general.fileutil import last_parts_file
from general.log import log_info, log_print, log_warning
from general.preview import Preview
from general.sql_coll import SQLcollector, SQLcollectors
from general.timeutil import TSC
from process.aapa_processor.aapa_processor import AAPARunnerContext

class MijlpaalDirsReEngineeringProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.sql = SQLcollectors()
        self.sql.add('mijlpaal_directories', SQLcollector({'update': {'sql':'update MIJLPAAL_DIRECTORIES set mijlpaal_type=?,kans=?,directory=?,datum=? where id=?'},
                                                           'delete': {'sql': 'delete from MIJLPAAL_DIRECTORIES where id=?'},}))
        self.sql.add('mijlpaal_directory_files', SQLcollector({'insert': {'sql':'insert into MIJLPAAL_DIRECTORY_FILES(mp_dir_id,file_id) values(?,?)'},
                                                               'delete': {'sql': 'delete from MIJLPAAL_DIRECTORY_FILES where mp_dir_id=?'},}))
    def _sql_delete_mijlpaal_directory_files(self, mp_dir: MijlpaalDirectory):
        self.sql.delete('mijlpaal_directory_files', [mp_dir.id])
    def _sql_delete_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self._sql_delete_mijlpaal_directory_files(mp_dir)
        self.sql.delete('mijlpaal_directories', [mp_dir.id])
    def _sql_update_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        for file in mp_dir.files_list:
            self.sql.insert('mijlpaal_directory_files', [mp_dir.id,file.id])
        self.sql.update('mijlpaal_directories', [mp_dir.mijlpaal_type,mp_dir.kans,
                                                 Roots.encode_path (mp_dir.directory), TSC.timestamp_to_sortable_str(mp_dir.datum), mp_dir.id])
    def process_student(self, student: Student, preview=False):      
        student_directory = self.student_dir_queries.find_student_dir(student)
        listing = {}
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        log_info(f'Student: {student}')
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
    def get_student_dirs(self, student: Student)->list[MijlpaalDirectory]:
        student_directory = self.student_dir_queries.find_student_dir(student)
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        dirs = self._check_doublures(student_directory.get_directories(mijlpaal_type=MijlpaalType.AANVRAAG, sorted=False))
        if dirs and len(dirs) > 1:
            return sorted(dirs, key=lambda d: d.id)
        else:
            return None
    
    # self.process_mijlpaal_directory(dir, student, preview=preview)
    def _get_all_directories(self)->dict:
        listing = {}
        for student in filter(lambda s: s.status in Student.Status.active_states(), self.storage.queries('studenten').find_all()):
            print(student.full_name)
            if (dirlist := self.get_student_dirs(student)):
                listing[student.email] = {'student': student, 'dirs': dirlist}
        return listing
    def _correct_student(self, student: Student, mp_dir_list: list[MijlpaalDirectory]):
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

    def process_all(self,  migrate_dir = None):        
        print('----------------------------------')
        for entry in self._get_all_directories().values():
            print(f'{entry['student']}:')
            for dir in entry['dirs']:
                filestr = "\n\t".join([Path(file.filename).name for file in dir.files_list]) if dir.files_list else '<No files>'
                print(f'{dir.id}-{dir.datum}: {last_parts_file(dir.directory,2)}\n\t{filestr}')
            self._correct_student(entry['student'], entry['dirs'])
            print('--- after ---')
            for dir in entry['dirs']:
                filestr = "\n\t".join([Path(file.filename).name for file in dir.files_list]) if dir.files_list else '<No files>'
                print(f'{dir.id}-{dir.datum}: {last_parts_file(dir.directory,2)}\n\t{filestr}')
            # self.process_student(student, preview=True)
        if migrate_dir:            
            filename = Path(migrate_dir).resolve().joinpath('correct_mp_dirs.json')
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')
def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--migrate', dest='migrate', type=str,help='create SQL output from e.g. detect or student in this directory') 
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    context.processing_options.debug = True
    context.processing_options.preview = True

    migrate_dir=namespace.migrate if 'migrate' in namespace else None
    print(migrate_dir)
    storage = context.configuration.storage
    with Preview(True,storage,'Corrigeer dubbelingen in mijlpaal_directories voor aanvragen (voor migratie)'):
        MijlpaalDirsReEngineeringProcessor(storage).process_all(migrate_dir)


