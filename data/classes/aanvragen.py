from __future__ import annotations
import datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from data.classes.bedrijven import Bedrijf
from data.classes.files import File
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Aanvraag(Milestone):
    Beoordeling = Milestone.Beoordeling
    class Status(IntEnum):
        DELETED         = -1
        NEW             = 0
        IMPORTED_PDF    = 1
        NEEDS_GRADING   = 2
        GRADED          = 3
        ARCHIVED        = 4 
        MAIL_READY      = 5
        READY           = 6
        READY_IMPORTED  = 7
        def __str__(self):
            STRS = {Aanvraag.Status.DELETED: 'verwijderd', Aanvraag.Status.NEW: 'nog niet bekend', Aanvraag.Status.IMPORTED_PDF: 'gelezen (PDF)',  
                    Aanvraag.Status.NEEDS_GRADING: 'te beoordelen', Aanvraag.Status.GRADED: 'beoordeeld', 
                    Aanvraag.Status.ARCHIVED: 'gearchiveerd', Aanvraag.Status.MAIL_READY: 'mail klaar voor verzending', Aanvraag.Status.READY: 'geheel verwerkt', 
                    Aanvraag.Status.READY_IMPORTED: 'verwerkt (ingelezen via Excel)'}
            return STRS[self.value]
    def __init__(self, student: Student, bedrijf: Bedrijf = None, datum_str='', titel='', source_info: File = None, datum: datetime.datetime = None, 
                 beoordeling=Beoordeling.TE_BEOORDELEN, status=Status.NEW, id=EMPTY_ID, kans=1):
        super().__init__(student=student, bedrijf=bedrijf, datum = datum, kans=kans, status=status, beoordeling=beoordeling, titel=titel, id=id)
        self.datum_str = datum_str
        if source_info:
            self._files.set_file(source_info)
            if not self.datum:
                self.datum = self.files.get_timestamp(File.Type.AANVRAAG_PDF)
        # else:
        #     self._files.reset()
        #     self.datum = None
    @property
    def timestamp(self):
        return self.datum #self.files.get_timestamp(File.Type.AANVRAAG_PDF)
    def timestamp_str(self):
        return TSC.timestamp_to_str(self.timestamp)
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
    def __eq__(self, value: Aanvraag):
        if  self.datum_str != value.datum_str:
            return False
        if  self.titel != value.titel:
            return False
        if  self.student != value.student:
            return False
        if  self.bedrijf != value.bedrijf:
            return False
        if  self.timestamp != value.timestamp:
            return False
        return True
    def valid(self):
        return self.student.valid() and self.bedrijf.valid() 
    @property 
    def datum_str(self):
        return self.__datum_str
    @datum_str.setter
    def datum_str(self, value):
        self.__datum_str = value.replace('\r', ' ').replace('\n', ' ')


