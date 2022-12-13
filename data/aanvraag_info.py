from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum
from pathlib import Path
from database.dbConst import EMPTY_ID
from general.date_parser import DateParser
from general.valid_email import is_valid_email


@dataclass
class Bedrijf:        
    bedrijfsnaam: str = ''
    id: int = EMPTY_ID #key
    def __str__(self): 
        return f'{self.id}:{self.bedrijfsnaam}'
    def valid(self):
        return self.bedrijfsnaam != ''
    def __eq__(self, value: Bedrijf) -> bool:        
        if  self.bedrijfsnaam != value.bedrijfsnaam:
            return False
        return True

class FileType(Enum):
    UNKNOWN      = -1
    AANVRAAG_PDF = 0
    EXPORT_XLSX  = 1
    OORDEEL_DOCX = 2
    OORDEEL_PDF  = 3
    MAIL_DOCX    = 4
    MAIL_HTM     = 5
    def __str__(self):
        STR_DICT = {FileType.UNKNOWN: '?', FileType.AANVRAAG_PDF: 'PDF-file (aanvraag)', FileType.EXPORT_XLSX: 'Excel file (summary)', 
                    FileType.OORDEEL_DOCX: 'Beoordeling (Word format)', FileType.OORDEEL_PDF: 'Beoordeling (Word format)', 
                    FileType.MAIL_DOCX: 'Mail message body (Word format)', FileType.MAIL_HTM: 'Mail message body (HTM format)'
                    }
        return STR_DICT.get(self, '!unknown')

AUTOTIMESTAMP = 0
class FileInfo:
    def _get_timestamp(filename: str)-> datetime.datetime:
        return datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime)
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    def __init__(self, filename: str, timestamp: datetime.datetime = AUTOTIMESTAMP, filetype: FileType=FileType.UNKNOWN):
        self.filename = str(filename) # to remove the WindowsPath label if needed
        if Path(filename).is_file() and timestamp == AUTOTIMESTAMP:
            self.timestamp = FileInfo._get_timestamp(filename)
        else:
            self.timestamp = timestamp
        self.filetype = filetype
    def __str__(self): 
        return f'{self.filename}: {str(self.filetype)} [{FileInfo.timestamp_to_str(self.timestamp)}]'    
    @property    
    def timestamp(self):
        return self._timestamp
    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = FileInfo.__rounded_timestamp(value)
    @staticmethod
    def __rounded_timestamp(value):
        #remove possible milliseconds so that the string can be read uniformly from the database if needed
        return FileInfo.str_to_timestamp(FileInfo.timestamp_to_str(value))
    @staticmethod
    def timestamp_to_str(value):
        return datetime.datetime.strftime(value, FileInfo.DATETIME_FORMAT)
    @staticmethod
    def str_to_timestamp(value):
        return datetime.datetime.strptime(value, FileInfo.DATETIME_FORMAT)
    def __eq__(self, value: FileInfo):
        if  self.filename != value.filename:
            return False
        if  self.timestamp != value.timestamp:            
            return False
        if  self.filetype != value.filetype:
            return False
        return True

class StudentInfo:
    def __init__(self, student_name='', studnr='', telno='', email=''):        
        self.student_name = student_name
        self.studnr = studnr #key
        self.telno = telno
        self.email = email
    def __str__(self):
        return f'{self.student_name}({self.studnr})'
    def __eq__(self, value: StudentInfo):
        if  self.student_name != value.student_name:
            return False
        if  self.studnr != value.studnr:
            return False
        if  self.telno != value.telno:
            return False
        if  self.email != value.email:
            return False
        return True
    @property
    def first_name(self):
        if self.student_name and (words := self.student_name.split(' ')):
            return words[0]
        return ''
    def valid(self):
        return self.student_name != '' and self.studnr != '' and is_valid_email(self.email) 

class AanvraagStatus(Enum):
    INITIAL         = 0
    NEEDS_GRADING   = 1
    GRADED          = 2
    MAIL_READY      = 3
    READY           = 4
    def __str__(self):
        STRS = {AanvraagStatus.INITIAL: 'ontvangen',  AanvraagStatus.NEEDS_GRADING: 'te beoordelen', AanvraagStatus.GRADED: 'beoordeeld', AanvraagStatus.MAIL_READY: 'mail klaar voor verzending', AanvraagStatus.READY: 'verwerkt'}
        return STRS[self]
        
class AanvraagBeoordeling(Enum):
    TE_BEOORDELEN = 0
    ONVOLDOENDE   = 1
    VOLDOENDE     = 2
    def __str__(self):
        STRS = {AanvraagBeoordeling.TE_BEOORDELEN: '', AanvraagBeoordeling.ONVOLDOENDE: 'onvoldoende', AanvraagBeoordeling.VOLDOENDE: 'voldoende'}
        return STRS[self]

class AanvraagInfo:
    def __init__(self, fileinfo: FileInfo, student: StudentInfo, bedrijf: Bedrijf = None, datum_str='', titel='', beoordeling=AanvraagBeoordeling.TE_BEOORDELEN, status=AanvraagStatus.INITIAL, id=EMPTY_ID, versie =1):        
        self.id = id
        self._dateparser = DateParser()
        self.fileinfo = fileinfo
        self.student = student
        self.bedrijf = bedrijf
        self.datum_str = datum_str
        self.titel = titel
        self.versie = versie
        self.beoordeling:AanvraagBeoordeling=beoordeling
        self.status:AanvraagStatus=status
    def __str__(self):
        versie_str = '' if self.versie == 1 else f'({self.versie})'
        s = f'{str(self.student)}{versie_str} - {self.datum_str}: {self.bedrijf.bedrijfsnaam} - "{self.titel}" [{str(self.status)}]'
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
        if  self.fileinfo != value.fileinfo:
            return False
        return True
    def valid(self):
        return self.student.valid() and self.bedrijf.valid() and self.fileinfo.filetype == FileType.AANVRAAG_PDF
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
        self.__datum_str = value
        self.__parse_datum()
    def __parse_datum(self):
        self.__datum,self.__versie = self._dateparser.parse_date(self.datum_str)
        if self.__versie and self.__versie.find('/') >= 0:
            self.__versie = self.__versie.replace('/','').strip()
