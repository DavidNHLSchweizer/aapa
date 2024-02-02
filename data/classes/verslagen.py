from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.bedrijven import Bedrijf
from data.classes.const import _UNKNOWN, MijlpaalBeoordeling, MijlpaalType
from data.classes.mijlpaal_base import MijlpaalGradeable
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Verslag(MijlpaalGradeable):
    class Status(IntEnum):
        LEGACY          = -2
        INVALID         = -1
        NEW             = 0
        NEEDS_GRADING   = 1
        MULTIPLE        = 2
        GRADED          = 3
        READY           = 4
        def __str__(self):
            STRS = {Verslag.Status.LEGACY: 'erfenis',Verslag.Status.INVALID: 'ongeldig', 
                    Verslag.Status.NEW: 'nieuw', Verslag.Status.NEEDS_GRADING: 'te beoordelen', 
                    Verslag.Status.MULTIPLE: 'bijlage',
                    Verslag.Status.GRADED: 'beoordeeld', 
                    Verslag.Status.READY: 'geheel verwerkt'}
            return STRS.get(self, _UNKNOWN)
        @staticmethod
        def valid_states()->set[Verslag.Status]:
            return {status for status in Verslag.Status} - {Verslag.Status.INVALID}
            
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
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
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

