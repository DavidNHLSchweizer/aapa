""" MOVE_FILES. 

    aanpassen van database: versplaats alle files van mijlpaaldirectories naar verslag en aanvraag.
    
    bedoeld voor migratie db naar versie 1.25
    
"""
import math
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from data.general.const import MijlpaalType
from database.classes.database import Database
from general.timeutil import TSC
from main.log import log_error
from process.general.preview import Preview
from storage.queries.student_directories import StudentDirectoriesQueries
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class MoveFilesProcessor(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql.add('aanvragen', SQLcollector({'insert': {'sql':'insert into AANVRAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,datum_str,versie) values(?,?,?,?,?,?,?,?,?,?)' , 'concatenate':False},}))
        sql.add('bedrijven', SQLcollector({'insert': {'sql':'insert into BEDRIJVEN(id,name) values(?,?)' },}))
        sql.add('verslagen', SQLcollector({'insert': {'sql':'insert into VERSLAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer) values(?,?,?,?,?,?,?,?,?,?)' },
                                           }))
        sql.add('aanvragen_details', SQLcollector({'insert': {'sql': self.insert_detail_query('AANVRAGEN', 'aanvraag_id'),},
                                                   }))                                                   
        sql.add('verslagen_details', SQLcollector({'insert': {'sql': self.insert_detail_query('VERSLAGEN', 'verslag_id'),},
                                                   }))                                                   
        sql.add('mijlpaal_directories_details', SQLcollector({'delete': {'sql': self.delete_detail_query('MIJLPAAL_DIRECTORIES', 'mp_dir_id'), 'concatenate': False},
                                                             'insert': {'sql': self.insert_detail_query('MIJLPAAL_DIRECTORIES', 'mp_dir_id'), }}                                                             
                                                             ))
        return sql
    def process_verslag(self, mp_dir: MijlpaalDirectory, verslag: Verslag):
        self.log(f'Verslag: {verslag.summary()}; Verslag id: {verslag.id}')
        for file in mp_dir.get_files():
            if not verslag.files.contains(file):
                self.sql.insert('verslagen_details', [verslag.id, file.id, self.file_code])
            self.sql.delete('mijlpaal_directories_details', [mp_dir.id, file.id, self.file_code])
    def process_aanvraag(self, mp_dir: MijlpaalDirectory, aanvraag: Aanvraag):
        self.log(f'Aanvraag: {aanvraag.summary()}; Aanvraag id: {aanvraag.id}')
        for file in mp_dir.get_files():
            if not aanvraag.files.contains(file):
                self.sql.insert('aanvragen_details', [aanvraag.id, file.id, self.file_code])
            self.sql.delete('mijlpaal_directories_details', [mp_dir.id, file.id, self.file_code])
    def _create_new_aanvraag(self, student: Student, mp_dir: MijlpaalDirectory)->Aanvraag:
        self.log(f'\tToevoegen ontbrekende aanvraag (dummy) voor {student}')
        new_aanvraag = Aanvraag(student=student, titel=f'{student.full_name} (dummy aanvraag)', bedrijf=self.bedrijf_onbekend, datum=mp_dir.datum, 
                                status=Aanvraag.Status.LEGACY)
        self.storage.crud('aanvragen').create(new_aanvraag)
        self.sql.insert('aanvragen',      
                        [new_aanvraag.id, TSC.timestamp_to_sortable_str(new_aanvraag.datum), 
                            new_aanvraag.student.id, self.bedrijf_onbekend.id,new_aanvraag.titel,
                            new_aanvraag.kans,new_aanvraag.status,new_aanvraag.beoordeling,
                            new_aanvraag.datum_str,new_aanvraag.versie])                                     
        self.sql.insert('mijlpaal_directories_details', [mp_dir.id, new_aanvraag.id, self.aanvraag_code])
        return new_aanvraag  
    def _create_new_verslag(self, student: Student, mp_dir: MijlpaalDirectory)->Verslag:
        self.log(f'\tToevoegen ontbrekend {mp_dir.mijlpaal_type} (dummy) voor {student}')
        new_verslag = Verslag(mijlpaal_type=mp_dir.mijlpaal_type,student=student, titel=f'{student.full_name} (dummy verslag)', 
                              bedrijf=self.bedrijf_onbekend, datum=mp_dir.datum, status=Verslag.Status.LEGACY)
#(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,verslag_type,cijfer)
        self.storage.crud('verslagen').create(new_verslag)
        self.sql.insert('verslagen',      
                        [new_verslag.id, TSC.timestamp_to_sortable_str(new_verslag.datum), 
                            new_verslag.student.id, self.bedrijf_onbekend.id,new_verslag.titel,
                            new_verslag.kans,new_verslag.status,new_verslag.beoordeling,
                            new_verslag.mijlpaal_type,math.pi])
        self.sql.insert('mijlpaal_directories_details', [mp_dir.id, new_verslag.id, self.verslag_code])
        return new_verslag  
    def process_aanvragen(self, mp_dir: MijlpaalDirectory):
        if aanvragen := mp_dir.mijlpalen.as_list('aanvragen'):
            for aanvraag in aanvragen:
                self.process_aanvraag(mp_dir, aanvraag)
        else: # aanvraag ontbreekt
            if not (student_dirs := self.student_dir_queries.find_student_dir_from_directory(mp_dir.directory)):
                log_error(f'Kan {File.display_file(mp_dir.directory)} niet koppelen aan student')
            else:
                self.process_aanvraag(mp_dir,self._create_new_aanvraag(student_dirs[0].student, mp_dir))
    def process_verslagen(self, mp_dir: MijlpaalDirectory):
        if verslagen := mp_dir.mijlpalen.as_list('verslagen'):
            for verslag in verslagen:
                self.process_verslag(mp_dir, verslag)       
        else: # verslag ontbreekt
            if not (student_dirs := self.student_dir_queries.find_student_dir_from_directory(Path(mp_dir.directory).parent)):
                log_error(f'Kan {File.display_file(mp_dir.directory)} niet koppelen aan student')
            else:
                self.log(f'\tToevoegen ontbrekend verslag (dummy) voor {student_dirs[0].student}')
                self.process_verslag(mp_dir,self._create_new_verslag(student_dirs[0].student, mp_dir))
    def process_mijlpaal_directory(self, mp_dir: MijlpaalDirectory):
        self.log(f'{File.display_file(mp_dir.directory)}:')
        if mp_dir.mijlpaal_type == MijlpaalType.AANVRAAG:
            self.process_aanvragen(mp_dir)
        elif mp_dir.mijlpaal_type.is_verslag() or mp_dir.mijlpaal_type.is_eindbeoordeling():
            self.process_verslagen(mp_dir)
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.student_dir_queries: StudentDirectoriesQueries = self.storage.queries('student_directories')
        self.database = context.storage.database
        self.file_code = ClassCodes.classtype_to_code(File)
        self.aanvraag_code = ClassCodes.classtype_to_code(Aanvraag)
        self.verslag_code = ClassCodes.classtype_to_code(Verslag)
        self.bedrijf_onbekend = Bedrijf('BZN: BedrijfZonderNaam')
        self.storage.ensure_key('bedrijven', self.bedrijf_onbekend)
        self.sql.insert('bedrijven', [self.bedrijf_onbekend.id, self.bedrijf_onbekend.name])
        return True
    def callback(self, msg: str, n: int)->bool:                
        match msg:
            case 'read many':
                if n % 100 == 50:
                    self.log(f'---{msg}: {n}---')
            case 'reading details':
                self._n_details += 1
                if self._n_details %50 == 0:
                    self.log(f'---{msg}: {self._n_details}---')
        return True
    def _get_mp_dirs(self)->list[MijlpaalDirectory]:
        self._n_details = 0
        # return self.storage.crud('mijlpaal_directories').read_many(set([585,615,657]))
        return self.storage.find_all('mijlpaal_directories',callback=self.callback)
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:        
        self.log(f'...collecting mijlpaal_directories...')
        all_mp_dirs = self._get_mp_dirs()
        self.log(f'ready. mijlpaal_directories collected.')
        with Preview(True,self.storage, 'dit moet altijd met preview'):
            for mp_dir in all_mp_dirs:
                self.process_mijlpaal_directory(mp_dir)
        return True
