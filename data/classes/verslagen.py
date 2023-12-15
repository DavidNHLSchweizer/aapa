from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from data.classes.const import _UNKNOWN, MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalBase
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Verslag(MijlpaalBase):
    class Status(IntEnum):
        NEW             = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        READY           = 3
        def __str__(self):
            STRS = {Verslag.Status.NEW: 'nieuw', Verslag.Status.NEEDS_GRADING: 'te beoordelen', Verslag.Status.GRADED: 'beoordeeld', 
                    Verslag.Status.READY: 'geheel verwerkt'}
            return STRS.get(self, _UNKNOWN)
    Type = MijlpaalType
    def __init__(self, mijlpaal_type: Verslag.Type, student:Student, file: File, datum: datetime.datetime, 
                 kans: int=1, id=EMPTY_ID, titel='', cijfer='', directory=''):
        super().__init__(student=student, datum=datum, status=Verslag.Status.NEW, titel=titel, allow_multiple=True, id=id)   
        self.verslag_type = mijlpaal_type     
        self.cijfer = ''
        self.directory = directory
        if file:
            self._files.add(file)
        self.kans=kans   
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        if self.beoordeling != Verslag.Beoordeling.TE_BEOORDELEN:
            s = s + f' ({str(self.beoordeling)})'
        file_str = "\n\t\t".join([file.summary(name_only=True) for file in self.files_list])
        if file_str:
            s = s + "\n\t\t"+ file_str
        return s
