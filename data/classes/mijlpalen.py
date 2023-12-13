from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.files import File
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Mijlpaal(Milestone):
    class Status(IntEnum):
        NEW             = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        READY           = 3
        def __str__(self):
            STRS = {Mijlpaal.Status.NEW: 'nieuw', Mijlpaal.Status.NEEDS_GRADING: 'te beoordelen', Mijlpaal.Status.GRADED: 'beoordeeld', 
                    Mijlpaal.Status.READY: 'geheel verwerkt'}
            return STRS[self.value]
    class Type(IntEnum):
        UNKNOWN             = 0
        PVA                 = 1
        ONDERZOEKS_VERSLAG  = 2
        TECHNISCH_VERSLAG   = 3
        EIND_VERSLAG        = 4
        PRODUCT_BEOORDELING = 6
        AFSTUDEER_ZITTING   = 5
        def __str__(self):
            _MT_STRS = {Mijlpaal.Type.UNKNOWN: '', Mijlpaal.Type.PVA: 'plan van aanpak', 
                        Mijlpaal.Type.ONDERZOEKS_VERSLAG: 'onderzoeksverslag', Mijlpaal.Type.TECHNISCH_VERSLAG: 'technisch verslag',
                        Mijlpaal.Type.EIND_VERSLAG: 'eindverslag', Mijlpaal.Type.AFSTUDEER_ZITTING: 'afstudeerzitting'
            }
            return _MT_STRS[self]
    def __init__(self, mijlpaal_type: Mijlpaal.Type, student:Student, file: File, datum: datetime.datetime, 
                 kans: int=1, id=EMPTY_ID, titel='', cijfer='', directory=''):
        super().__init__(student=student, datum=datum, status=Mijlpaal.Status.NEW, titel=titel, id=id)   
        self.mijlpaal_type = mijlpaal_type     
        self.cijfer = ''
        self.directory = directory
        if file:
            self._files.add(file)
        self.kans=kans
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        if self.beoordeling != '':
            s = s + f' ({str(self.beoordeling)})'
        return s

