""" CREATE_VERSLAGEN

    Maakt de verslagen aan in de al eerder gedetecteerde student-directories. De verslagen waren nog niet 
    in de database aangemaakt.
    Dit wordt gedaan voor alle studenten. Voor afgestudeerde studenten kan vaak de aanvraag (en daarmee het bedrijf en de titel) 
    niet worden gevonden in de database. Omdat deze afgestudeerde studenten niet van belang zijn voor verdere processing wordt hier niets aan gedaan.

    De code is bedoeld voor de migratie naar database versie 1.24
    Verschil met versie voor 1.123 is dat er rekening wordt gehouden met de mogelijkheid dat het verslag al is geimporteerd. 

"""
from data.classes.aanvragen import Aanvraag
from data.general.const import FileType, MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from storage.queries.aanvragen import AanvraagQueries
from storage.queries.student_directories import StudentDirectoryQueries
from main.log import log_info, log_warning
from general.timeutil import TSC
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext
from storage.queries.verslagen import VerslagQueries

class VerslagenReEngineeringProcessor(MigrationPlugin):
    def init_SQLcollectors(self)->SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('verslagen', SQLcollector({'insert': {'sql':'insert into VERSLAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type) values(?,?,?,?,?,?,?,?,?)' },
                                           'delete': {'sql':'delete from VERSLAGEN where id in (?)'}                                           
                                           }))
        sql.add('verslagen_files', SQLcollector({'insert': {'sql':'insert into VERSLAGEN_FILES(verslag_id,file_id) values(?,?)' },}))
        return sql
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
        self.log(f'\tVerslag {verslag}')
        self.storage.queries('verslagen').ensure_key(verslag)            
        self.sql.insert('verslagen_files', [verslag.id, file.id])
        # this was no done in the m123 migration
        if self.verslag_queries.find_verslag(verslag):
            return # this for some reason is already in the database, can't imagine why though
        if not preview:
            self.storage.crud('verslagen').create(verslag)    
        self.sql.insert('verslagen', [verslag.id,TSC.timestamp_to_sortable_str(verslag.datum),verslag.student.id,
                                      verslag.bedrijf.id if bedrijf else -1, titel,
                                      verslag.kans,verslag.status,verslag.beoordeling,verslag.mijlpaal_type
                                      ])
    def process_mijlpaal_directory(self, mp_dir: MijlpaalDirectory, student: Student, preview=False):
        if not mp_dir.mijlpaal_type.is_verslag():
            return
        known_verslagen = self.verslag_queries.find_values(['student', 'mijlpaal_type', 'kans'], [student,mp_dir.mijlpaal_type, mp_dir.kans], True)
        existing_verslag = known_verslagen[0] if known_verslagen else None
        for file in mp_dir.files.files:
            if file.filetype == mp_dir.mijlpaal_type.default_filetype():         
                if existing_verslag:       
                    self.sql.insert('verslagen_files', [existing_verslag.id,file.id])
                else:
                    self.create_verslag(mp_dir, student, file, preview=preview)
        if existing_verslag: 
            for verslag in known_verslagen[1:]:
                self.sql.delete('verslagen', [verslag.id])                    
    def process_student(self, student: Student, preview=False):      
        student_dir_queries: StudentDirectoryQueries = self.storage.queries('student_directories')
        student_directory = student_dir_queries.find_student_dir(student)
        if not student_directory:
            log_warning(f'Geen directory gevonden voor student {student}.')
            return
        log_info(f'Student: {student}', to_console=True)
        for mp_dir in student_directory.directories:
            self.process_mijlpaal_directory(mp_dir, student, preview=preview)
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.verslag_queries: VerslagQueries = self.storage.queries('verslagen')
        return True
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:          
        for student in self.storage.queries('studenten').find_all():
            self.process_student(student, preview=True)
        return True
