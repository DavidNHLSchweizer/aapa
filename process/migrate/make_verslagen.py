
from pathlib import Path
from typing import Tuple
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.classes.const import FileType
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.aanvragen import AanvraagQueries
from data.storage.queries.base_dirs import BaseDirQueries
from data.storage.queries.student_directories import StudentDirectoryQueries
from general.log import log_error, log_info, log_print, log_warning
from general.timeutil import TSC
from migrate.sql_coll import SQLcollector, SQLcollectors
from process.general.student_dir_builder import StudentDirectoryBuilder


class VerslagenReEngineeringProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.sql = SQLcollectors()
        self.sql.add('verslagen', SQLcollector({'insert': {'sql':'insert into VERSLAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type) values(?,?,?,?,?,?,?,?,?)' },}))
    def _get_aanvraag(self, student: Student)->Aanvraag:
        aanvraag_queries:AanvraagQueries = self.storage.queries('aanvragen')
        aanvraag = aanvraag_queries.find_student_aanvraag(student)
        if not aanvraag:
            log_warning(f'Afstudeerbedrijf kan niet worden gevonden: Geen aanvraag gevonden voor student {student}.')
        return aanvraag
    def create_verslag(self, mp_dir: MijlpaalDirectory, student: Student, file: File, preview=False):
        if (aanvraag:= self._get_aanvraag(student)):
            bedrijf = aanvraag.bedrijf
            titel = aanvraag.titel
        else:
            bedrijf = None
            titel = 'Onbekend'
        verslag = Verslag(mijlpaal_type=mp_dir.mijlpaal_type, student=student, datum = file.timestamp, 
                          bedrijf = bedrijf,
                          kans = mp_dir.kans, status=Verslag.Status.LEGACY, titel=titel
                          )
        log_print(f'\tVerslag {verslag}')
        self.storage.queries('verslagen').ensure_key(verslag)            
        if not preview:
            self.storage.crud('verslagen').create(verslag)    
        self.sql.insert('verslagen', [verslag.id,TSC.timestamp_to_sortable_str(verslag.datum),verslag.student.id,
                                      verslag.bedrijf.id if bedrijf else -1, titel,
                                      verslag.kans,verslag.status,verslag.beoordeling,verslag.mijlpaal_type
                                      ])
    def process_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, student: Student, preview=False):
        for file in mp_dir.files.files:
            match file.filetype:
                case FileType.PVA | FileType.ONDERZOEKS_VERSLAG | FileType.TECHNISCH_VERSLAG | FileType.EIND_VERSLAG:
                    self.create_verslag(mp_dir, student, file, preview=preview)
                case _: continue                    
    def process_student(self, student: Student, preview=False):      
        student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        student_directory = student_dir_queries.find_student_dir(student)
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        log_info(f'Student: {student}')
        for mp_dir in student_directory.directories:
            self.process_mijlpaal_directory(mp_dir, student, preview=preview)
    def process_all(self,  migrate_dir = None):        
        for student in self.storage.queries('studenten').find_all():
            self.process_student(student, preview=True)
        if migrate_dir:
            filename = Path(migrate_dir).resolve().joinpath('create_verslagen.json')
            self.sql.dump_to_file(filename)
            log_print(f'SQL data dumped to file {filename}')


