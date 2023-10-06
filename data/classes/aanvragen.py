from __future__ import annotations
from enum import IntEnum
from pathlib import Path
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.date_parser import DateParser
from general.timeutil import TSC

class Aanvraag:
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
    class Beoordeling(IntEnum):
        TE_BEOORDELEN = 0
        ONVOLDOENDE   = 1
        VOLDOENDE     = 2
        def __str__(self):
            _AB_STRS = {Aanvraag.Beoordeling.TE_BEOORDELEN: '', Aanvraag.Beoordeling.ONVOLDOENDE: 'onvoldoende', Aanvraag.Beoordeling.VOLDOENDE: 'voldoende'}
            return _AB_STRS[self]
        @staticmethod
        def from_str(string)->Aanvraag.Beoordeling:
            for beoordeling in Aanvraag.Beoordeling:                
                if string == str(beoordeling):
                    return beoordeling
            return None
    def __init__(self, student: Student, bedrijf: Bedrijf = None, datum_str='', titel='', source_info: File = None, 
                 beoordeling=Beoordeling.TE_BEOORDELEN, status=Status.NEW, id=EMPTY_ID, aanvraag_nr = 1):        
        self._id = id
        self.student = student
        self.bedrijf = bedrijf
        self.datum_str = datum_str
        self._files = Files(id)
        if source_info:
            self._files.set_file(source_info)
        else:
            self._files.reset()
        self.titel = titel
        self.aanvraag_nr = aanvraag_nr
        self.beoordeling = beoordeling
        self.status = status
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        self._id = value
        self._files.aanvraag_id = value
    @property
    def files(self)->Files:
        return self._files
    @files.setter
    def files(self, files: Files):
        for ft in File.Type:
            if ft != File.Type.UNKNOWN:
                self.files.set_file(files.get_file(ft))
    @property
    def timestamp(self):
        return self.files.get_timestamp(File.Type.AANVRAAG_PDF)
    def timestamp_str(self):
        return TSC.timestamp_to_str(self.timestamp)
    def aanvraag_source_file_name(self):
        return Path(self.files.get_filename(File.Type.AANVRAAG_PDF))
    def summary(self)->str:
        return f'{str(self.student)} ({self.bedrijf.name})-{self.titel}'    
    def __str__(self):
        versie_str = '' if self.aanvraag_nr == 1 else f'({self.aanvraag_nr})'
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
    def student_versie(self):
        return self.__versie
    @property 
    def datum_str(self):
        return self.__datum_str
    @datum_str.setter
    def datum_str(self, value):
        self.__datum_str = value.replace('\r', ' ').replace('\n', ' ')
    def register_file(self, filename: str, filetype: File.Type):
        self.files.set_file(File(filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, aanvraag_id=self.id))
    def unregister_file(self, filetype: File.Type):
        self.files.reset_file(filetype)


