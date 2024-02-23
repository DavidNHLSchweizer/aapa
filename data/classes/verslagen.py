from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.bedrijven import Bedrijf
from data.general.const import _UNKNOWN, MijlpaalBeoordeling, MijlpaalType, VerslagStatus
from data.classes.mijlpaal_base import MijlpaalGradeable
from data.classes.studenten import Student
from database.classes.dbConst import EMPTY_ID
from general.timeutil import TSC

class Verslag(MijlpaalGradeable):
    Status = VerslagStatus            
# def __init__(self, student: Student, bedrijf: Bedrijf = None, datum_str='', titel='', 
#                  source_info: File = None, datum: datetime.datetime = None, 
#                  beoordeling=Beoordeling.TE_BEOORDELEN, status=Status.NEW, id=EMPTY_ID, kans=0, versie=1):

    Type = MijlpaalType
    def __init__(self, mijlpaal_type: Verslag.Type, student:Student, datum: datetime.datetime,  bedrijf: Bedrijf=None,
                 kans:int=1, beoordeling=MijlpaalBeoordeling.TE_BEOORDELEN, status=Status.NEW, id=EMPTY_ID, titel='', cijfer=''):
        super().__init__(mijlpaal_type=mijlpaal_type, 
                         student=student, datum = datum, bedrijf=bedrijf, kans=kans, 
                         status=status, beoordeling=beoordeling, titel=titel, id=id)
        self.files.allow_multiple = True 
        self.cijfer = ''
    def summary(self)->str:
        return f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {self.student.full_name} ' +\
              f'"{self.titel}" [{str(self.status)}]'
    def __str__(self):        
        s = self.summary()
        if self.beoordeling != Verslag.Beoordeling.TE_BEOORDELEN:
            s = s + f' {self.cijfer=} {str(self.beoordeling)})'
        file_str = "\n\t\t".join([file.summary(name_only=True) for file in self.files_list])
        if file_str:
            s = s + "\n\t\t"+ file_str
        return s
    def __eq__(self, value2: Verslag):      
        if not super().__eq__(value2):
            return False
        if self.cijfer  != value2.cijfer:
            return False
        return True    

