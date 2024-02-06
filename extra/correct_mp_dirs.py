""" CORRECT_MP_DIRS. 

    aanpassen van database voor dubbelingen in mijlpaal_directories voor aanvragen.
    bedoeld voor migratie naar versie 1.23
    
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from data.classes.const import MijlpaalType
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.storage.aapa_storage import AAPAStorage
from data.storage.queries.student_directories import StudentDirectoryQueries
from general.log import log_info, log_print, log_warning
from general.preview import Preview
from general.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext

class MijlpaalDirsReEngineeringProcessor:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        self.sql = SQLcollectors()
        # self.sql.add('verslagen', SQLcollector({'insert': {'sql':'insert into VERSLAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type) values(?,?,?,?,?,?,?,?,?)' },}))
    # def _get_aanvraag(self, student: Student)->Aanvraag:
    #     aanvraag_queries:AanvraagQueries = self.storage.queries('aanvragen')
    #     aanvraag = aanvraag_queries.find_student_aanvraag(student)
    #     if not aanvraag:
    #         log_warning(f'Afstudeerbedrijf kan niet worden gevonden: Geen aanvraag gevonden voor student {student}.')
    #     return aanvraag
    # def create_verslag(self, mp_dir: MijlpaalDirectory, student: Student, file: File, preview=False):
    #     if (aanvraag:= self._get_aanvraag(student)):
    #         bedrijf = aanvraag.bedrijf
    #         titel = aanvraag.titel
    #     else:
    #         bedrijf = None
    #         titel = 'Onbekend'
    #     verslag = Verslag(mijlpaal_type=mp_dir.mijlpaal_type, student=student, datum = file.timestamp, 
    #                       bedrijf = bedrijf,
    #                       kans = mp_dir.kans, status=Verslag.Status.LEGACY, titel=titel
    #                       )
    #     log_print(f'\tVerslag {verslag}')
    #     self.storage.queries('verslagen').ensure_key(verslag)            
    #     if not preview:
    #         self.storage.crud('verslagen').create(verslag)    
    #     self.sql.insert('verslagen', [verslag.id,TSC.timestamp_to_sortable_str(verslag.datum),verslag.student.id,
    #                                   verslag.bedrijf.id if bedrijf else -1, titel,
    #                                   verslag.kans,verslag.status,verslag.beoordeling,verslag.mijlpaal_type
    #                                   ])
    # def process_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, student: Student, preview=False):
    #     for file in mp_dir.files.files:
    #         match file.filetype:
    #             case FileType.PVA | FileType.ONDERZOEKS_VERSLAG | FileType.TECHNISCH_VERSLAG | FileType.EIND_VERSLAG:
    #                 self.create_verslag(mp_dir, student, file, preview=preview)
    #             case _: continue                    
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
            return dirs
        else:
            return None
    
    # self.process_mijlpaal_directory(dir, student, preview=preview)
Dit geeft alvast een lijstje van studenten waar een correctie op moet komen. De correctie moet nog even wat helderder worden gechekt
    def process_all(self,  migrate_dir = None):        
        listing = {}
        for student in filter(lambda s: s.status in Student.Status.active_states(), self.storage.queries('studenten').find_all()):
            print(student.full_name)
            if (dirlist := self.get_student_dirs(student)):
                listing[student.full_name] = dirlist
        
        for student,listje in listing.items():
            # print(f'{student}: {[mpd.summary() for mpd in listje]}')
            print(f'{student}: {len(listje)}')

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
    storage = context.configuration.storage
    with Preview(True,storage,'Corrigeer dubbelingen in mijlpaal_directories voor aanvragen (voor migratie)'):
        MijlpaalDirsReEngineeringProcessor(storage).process_all(migrate_dir)


