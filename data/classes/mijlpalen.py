from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.const import MijlpaalType
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
    Type = MijlpaalType
    def __init__(self, mijlpaal_type: Mijlpaal.Type, student:Student, file: File, datum: datetime.datetime, 
                 kans: int=1, id=EMPTY_ID, titel='', cijfer='', directory=''):
        super().__init__(student=student, datum=datum, status=Mijlpaal.Status.NEW, titel=titel, id=id)   
        self.mijlpaal_type = mijlpaal_type     
        self.cijfer = ''
        self.directory = directory
        if file:
            self._files.add(file)
        self.kans=kans
   
    def default_filetype(self)->File.Type:
        match self.mijlpaal_type:
            case Mijlpaal.Type.PVA: return File.Type.PVA
            case Mijlpaal.Type.ONDERZOEKS_VERSLAG: return File.Type.ONDERZOEKS_VERSLAG
            case Mijlpaal.Type.TECHNISCH_VERSLAG: return File.Type.TECHNISCH_VERSLAG
            case Mijlpaal.Type.EIND_VERSLAG: return File.Type.EIND_VERSLAG
            case _: return File.Type.UNKNOWN
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        if self.beoordeling != '':
            s = s + f' ({str(self.beoordeling)})'
        return s

