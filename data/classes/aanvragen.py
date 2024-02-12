from __future__ import annotations
import datetime
from pathlib import Path
from data.classes.bedrijven import Bedrijf
from data.general.const import AanvraagStatus, MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalGradeable
from data.classes.studenten import Student
from database.classes.dbConst import EMPTY_ID

class Aanvraag(MijlpaalGradeable):
    Beoordeling = MijlpaalGradeable.Beoordeling
    Status = AanvraagStatus
    def __init__(self, student: Student, bedrijf: Bedrijf = None, datum_str='', titel='', 
                 source_info: File = None, datum: datetime.datetime = None, 
                 beoordeling=Beoordeling.TE_BEOORDELEN, status=Status.NEW, id=EMPTY_ID, kans=0, versie=1):
        super().__init__(mijlpaal_type=MijlpaalType.AANVRAAG, 
                         student=student, bedrijf=bedrijf, datum = datum, kans=kans, 
                         status=status, beoordeling=beoordeling, titel=titel, id=id)
        self.files.allow_multiple = False 
        self._datum_str = datum_str
        self.versie=versie
        if source_info:
            self._files.add(source_info)
            if not self.datum:
                self.datum = self.files.get_timestamp(File.Type.AANVRAAG_PDF)
    @property
    def timestamp(self): return self.datum 
    def aanvraag_source_file_path(self)->Path:
        return Path(self.files.get_filename(File.Type.AANVRAAG_PDF))
    def source_file_name(self)->str:
        return str(self.aanvraag_source_file_path())
    def summary(self)->str:
        return f'{str(self.student)} ({self.bedrijf.name})-{self.titel}'    
    def file_summary(self)->str:
        return self.summary() + "-files:\n" + self.files.summary()
    def __str__(self):
        versie_str = '' if self.kans == 1 else f'({self.kans})'
        s = f'{str(self.student)}{versie_str} - {self.datum_str}: {self.bedrijf.name} - "{self.titel}" [{str(self.status)}]'        
        if self.beoordeling != Aanvraag.Beoordeling.TE_BEOORDELEN:
            s = s + f' ({str(self.beoordeling)})'
        return s
    def __eq__(self, value2: Aanvraag):      
        if not super().__eq__(value2):
            return False
        if self.datum_str != value2.datum_str:
            return False
        if self.timestamp != value2.timestamp:
            return False
        return True    
    def valid(self):
        return self.student.valid() and self.bedrijf.valid() 
    @property 
    def datum_str(self):
        return self._datum_str
    @datum_str.setter
    def datum_str(self, value):
        self._datum_str = value.replace('\r', ' ').replace('\n', ' ')


