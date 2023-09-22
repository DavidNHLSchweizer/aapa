from __future__ import annotations
from enum import IntEnum
from pathlib import Path
from data.classes.bedrijven import Bedrijf
from data.classes.files import FileInfo, FileInfos, FileType
from data.classes.studenten import StudentInfo
from database.dbConst import EMPTY_ID
from general.date_parser import DateParser
from general.timeutil import TSC

class AanvraagStatus(IntEnum):
    INITIAL         = 0
    NEEDS_GRADING   = 1
    GRADED          = 2
    ARCHIVED        = 3 
    MAIL_READY      = 4
    READY           = 5
    READY_IMPORTED  = 6
    def __str__(self):
        STRS = {AanvraagStatus.INITIAL: 'ontvangen',  AanvraagStatus.NEEDS_GRADING: 'te beoordelen', AanvraagStatus.GRADED: 'beoordeeld', 
                AanvraagStatus.MAIL_READY: 'mail klaar voor verzending', AanvraagStatus.READY: 'verwerkt', 
                AanvraagStatus.READY_IMPORTED: 'verwerkt (ingelezen via Excel)', AanvraagStatus.ARCHIVED: 'gearchiveerd'}
        return STRS[self]
        
class AanvraagBeoordeling(IntEnum):
    TE_BEOORDELEN = 0
    ONVOLDOENDE   = 1
    VOLDOENDE     = 2
    def __str__(self):
        return _AB_STRS[self]
    @staticmethod
    def from_str(string)->AanvraagBeoordeling:
        for key,value in _AB_STRS.items():
            if string == value:
                return key
        return None
_AB_STRS = {AanvraagBeoordeling.TE_BEOORDELEN: '', AanvraagBeoordeling.ONVOLDOENDE: 'onvoldoende', AanvraagBeoordeling.VOLDOENDE: 'voldoende'}

class AanvraagInfo:
    def __init__(self, student: StudentInfo, bedrijf: Bedrijf = None, datum_str='', titel='', source_info: FileInfo = None, 
                 beoordeling=AanvraagBeoordeling.TE_BEOORDELEN, status=AanvraagStatus.INITIAL, id=EMPTY_ID, aanvraag_nr = 1):        
        self._id = id
        self._dateparser = DateParser()
        self.student = student
        self.bedrijf = bedrijf
        self.datum_str = datum_str
        self._files = FileInfos(id)
        if source_info:
            self._files.set_info(source_info)
        else:
            self._files.reset()
        self.titel = titel
        self.aanvraag_nr = aanvraag_nr
        self.beoordeling:AanvraagBeoordeling=beoordeling
        self.status:AanvraagStatus=status
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        self._id = value
        self._files.aanvraag_id = value
    @property
    def files(self)->FileInfos:
        return self._files
    @files.setter
    def files(self, files: FileInfos):
        for ft in FileType:
            if ft != FileType.UNKNOWN:
                self.files.set_info(files.get_info(ft))
    @property
    def timestamp(self):
        return self.files.get_timestamp(FileType.AANVRAAG_PDF)
    def timestamp_str(self):
        return TSC.timestamp_to_str(self.timestamp)
    @property
    def digest(self):
        return self.files.get_digest(FileType.AANVRAAG_PDF)
    def aanvraag_source_file_name(self):
        return Path(self.files.get_filename(FileType.AANVRAAG_PDF))
    def summary(self)->str:
        return f'{str(self.student)} ({self.bedrijf.name})-{self.titel}'    
    def __str__(self):
        versie_str = '' if self.aanvraag_nr == 1 else f'({self.aanvraag_nr})'
        s = f'{str(self.student)}{versie_str} - {self.datum_str}: {self.bedrijf.name} - "{self.titel}" [{str(self.status)}]'        
        if self.beoordeling != AanvraagBeoordeling.TE_BEOORDELEN:
            s = s + f' ({str(self.beoordeling)})'
        return s
    def __eq__(self, value: AanvraagInfo):
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
    def datum(self): 
        return self.__datum
    @property
    def student_versie(self):
        return self.__versie
    @property 
    def datum_str(self):
        return self.__datum_str
    @datum_str.setter
    def datum_str(self, value):
        self.__datum_str = value.replace('\r', ' ').replace('\n', ' ')
        self.__parse_datum()
    def __parse_datum(self):
        self.__datum,self.__versie = self._dateparser.parse_date(self.datum_str)
        if self.__versie and self.__versie.find('/') >= 0:
            self.__versie = self.__versie.replace('/','').strip()
    def register_file(self, filename: str, filetype: FileType):
        self.files.set_info(FileInfo(filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, aanvraag_id=self.id))
    def unregister_file(self, filetype: FileType):
        self.files.reset_info(filetype)


