""" CORRECT_STUD_DIRS. 

    aanpassen van database voor verkeerde student-directory koppelingen.
    (twee studenten: Marle Mulder, Jarno vd Poll)

    bedoeld voor migratie naar versie 1.23
    
"""
from data.classes.files import File
from data.classes.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.roots import Roots
from data.storage.queries.student_directories import StudentDirectoryQueries
from general.fileutil import last_parts_file
from general.log import log_info
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.aapa_processor.aapa_processor import AAPARunnerContext
from process.general.student_dir_builder import StudentDirectoryBuilder

class StudDirsReEngineeringProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('student_directories', SQLcollector({'insert': {'sql': 'insert into STUDENT_DIRECTORIES(id,stud_id,directory,basedir_id,status) values(?,?,?,?,?)'},
                                                          'update': {'sql': 'update STUDENT_DIRECTORIES set status=? where id=?'},                                                          
                                                          }))
        
        sql.add('student_directory_directories', SQLcollector({'delete': {'sql': 'delete from STUDENT_DIRECTORY_DIRECTORIES where stud_dir_id=? and mp_dir_id=?', 'concatenate':False},
                                                                    'insert': {'sql':'insert into STUDENT_DIRECTORY_DIRECTORIES(stud_dir_id, mp_dir_id) values(?,?)'},                                                                    
                                                                    }))
        return sql
    def create_sql_incorrect_mijlpaal_directories(self, old_student_dir: StudentDirectory, new_student_dir: StudentDirectory, new_mijlpaal_dir: MijlpaalDirectory):
        if old_student_dir.id != new_student_dir.id:
            self.sql.update('student_directories', [StudentDirectory.Status.ARCHIVED, old_student_dir.id])
            if old_student_dir.data.contains(new_mijlpaal_dir):
                self.sql.delete('student_directory_directories', [old_student_dir.id, new_mijlpaal_dir.id])
        self.sql.insert('student_directories', [new_student_dir.id, new_student_dir.student.id, Roots.encode_path(new_student_dir.directory), new_student_dir.base_dir.id, new_student_dir.status])
        self.sql.insert('student_directory_directories', [new_student_dir.id, new_mijlpaal_dir.id])

    def _process_incorrect_mijlpaal_directories(self):
        # inconsistente mijlpaal directories
        query = "select S.id as stud_id,full_name,SD.id as SD_id,SD.directory as stud_dir,MPD.id as mp_id,MPD.directory as mp_directory,F.ID as file_id,F.filename \
from studenten as S inner join STUDENT_DIRECTORIES as SD on SD.stud_id = S.ID inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.ID = SDD.stud_dir_id \
inner join MIJLPAAL_DIRECTORIES as MPD on MPD.id = SDD.mp_dir_id \
inner join MIJLPAAL_DIRECTORY_FILES as MPDF on MPD.id = MPDF.mp_dir_id \
inner join FILES as F on F.id = MPDF.file_id \
where (MPD.mijlpaal_type = ? and stud_dir <> mp_directory) or \
(SD.status=? and substr(F.filename,1,8) <> substr(MPD.directory,1,8))"

#first where catches cases (there were two) where student directory misaligned with mijlpaaldirectory
#second where catches cases (there is only one) where file placed in wrong directory caused correct results but \\
#wrong directory in RL.
        
        database = self.storage.database
        builder = StudentDirectoryBuilder(self.storage)
        student_dir_queries:StudentDirectoryQueries = self.storage.queries('student_directories')
        rows = database._execute_sql_command(query, [int(MijlpaalType.AANVRAAG),StudentDirectory.Status.ACTIVE],True)
        old_student = None
        for row in rows:
            student:Student = self.storage.crud('studenten').read(row['stud_id'])
            file:File = self.storage.crud('files').read(row['file_id'])
            log_info(f'Correcting for {student.full_name}: {last_parts_file(file.filename)}', self.verbose)
            if student != old_student:
                old_stud_dir = student_dir_queries.find_student_dir(student)
                old_student = student            
            (new_stud_dir, new_mp_dir) = builder.register_file(student,datum=file.timestamp,filename=file.filename,filetype=file.filetype,
                                               mijlpaal_type=MijlpaalType.AANVRAAG)
            self.create_sql_incorrect_mijlpaal_directories(old_stud_dir, new_stud_dir, new_mp_dir)
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        self._process_incorrect_mijlpaal_directories()
        return True

