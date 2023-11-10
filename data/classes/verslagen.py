from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from data.classes.files import File
from data.classes.milestones import StuMiType, StudentMilestone
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Verslag(StudentMilestone):
    class Status(IntEnum):
        NEW             = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        READY           = 3
        def __str__(self):
            STRS = {Verslag.Status.NEW: 'nieuw', Verslag.Status.NEEDS_GRADING: 'te beoordelen', Verslag.Status.GRADED: 'beoordeeld', 
                    Verslag.Status.READY: 'geheel verwerkt'}
            return STRS[self.value]
    class Status(IntEnum):
        NEW             = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        READY           = 3
        def __str__(self):
            STRS = {Verslag.Status.NEW: 'nieuw', Verslag.Status.NEEDS_GRADING: 'te beoordelen', Verslag.Status.GRADED: 'beoordeeld', 
                    Verslag.Status.READY: 'geheel verwerkt'}
            return STRS[self.value]
    def __init__(self, verslag_type: StuMiType, student:Student, file: File, datum: datetime.datetime, kans: int=1, id=EMPTY_ID, titel='', cijfer=''):
        super().__init__(milestone_type=verslag_type, student=student, datum=datum, status=Verslag.Status.NEW, titel=titel, id=id)        
        self.cijfer = ''
        if file:
            self._files.set_file(file)
            self.directory = str(Path(file.filename).parent)
        else:
            self._files.reset()
            self.directory = ''
        self.kans=kans
    @property
    def verslag_type(self)->StuMiType:
        return self.milestone_type
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.verslag_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        if self.beoordeling != '':
            s = s + f' ({str(self.beoordeling)})'
        return s

