from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from data.classes.files import File
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from process.scan.importing.filename_parser import FilenameParser

class Verslag(Milestone):
    class Status(IntEnum):
        NEW             = 0
        NEEDS_GRADING   = 1
        GRADED          = 2
        READY           = 3
        def __str__(self):
            STRS = {Verslag.Status.NEW: 'nog niet bekend', Verslag.Status.NEEDS_GRADING: 'te beoordelen', Verslag.Status.GRADED: 'beoordeeld', 
                    Verslag.Status.READY: 'geheel verwerkt'}
            return STRS[self.value]
    def __init__(self, type_description: str, student:Student, file: File, datum: datetime.datetime, kans: str, id=EMPTY_ID, titel=''):
        super().__init__(type_description=type_description, student=student, status=Verslag.Status.NEW, titel=titel, id=id)
        self.datum = datum
        if file:
            self._files.set_file(file)
        else:
            self._files.reset()
        self.kans=kans
    @classmethod
    def create_from_parsed(cls, filename: str, parsed: FilenameParser.Parsed)->Verslag:  
        return cls(type_description=parsed.product_type, student=Student(parsed.student_name, email=parsed.email), file=File(filename), 
                   datum=parsed.datum, kans=parsed.kans, titel=Path(parsed.original_filename).stem)  
    def __str__(self):        
        s = f'{datetime.datetime.strftime(self.datum, "%d-%m-%Y %H:%M:%S")}: {self.type_description} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        if self.beoordeling != '':
            s = s + f' ({str(self.beoordeling)})'
        return s
