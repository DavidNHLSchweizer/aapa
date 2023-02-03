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
    UNKNOWN             = -1
    AANVRAAG_PDF        = 0
    INVALID_PDF         = 1
    TO_BE_GRADED_DOCX   = 2
    GRADED_DOCX         = 3
    GRADED_PDF          = 4
    COPIED_PDF          = 5
    def __str__(self):
        STR_DICT = {FileType.UNKNOWN: '?', FileType.AANVRAAG_PDF: 'PDF-file (aanvraag)',  
                    FileType.TO_BE_GRADED_DOCX: 'Formulier beoordeling (Word format)', FileType.GRADED_DOCX: 'Ingevuld formulier beoordeling (Word format)', FileType.GRADED_PDF: 'Ingevuld formulier beoordeling (PDF format)', FileType.COPIED_PDF: 'Kopie van PDF-file (aanvraag)'
                    }
        return STR_DICT.get(self, '!unknown')

AUTOTIMESTAMP = 0
class FileInfo:
    @staticmethod
    def get_timestamp(filename: str)-> datetime.datetime:
        return FileInfo.__rounded_timestamp(datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime))
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    def __init__(self, filename: str, timestamp: datetime.datetime = AUTOTIMESTAMP, filetype: FileType=FileType.UNKNOWN, aanvraag_id=EMPTY_ID):
        self.filename = str(filename) # to remove the WindowsPath label if needed
        if Path(filename).is_file() and timestamp == AUTOTIMESTAMP:
            self.timestamp = FileInfo.get_timestamp(filename)
        else:
            self.timestamp = timestamp
        self.filetype = filetype
        self.aanvraag_id = aanvraag_id
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
        return FileInfo.str_to_timestamp(FileInfo.timestamp_to_str(value)) if value != AUTOTIMESTAMP else AUTOTIMESTAMP
    @staticmethod
    def timestamp_to_str(value):        
        return datetime.datetime.strftime(value, FileInfo.DATETIME_FORMAT) if value != AUTOTIMESTAMP else '' 
    @staticmethod
    def str_to_timestamp(value):
        return datetime.datetime.strptime(value, FileInfo.DATETIME_FORMAT) if value else AUTOTIMESTAMP
    def __eq__(self, value: FileInfo):
        if  self.filename != value.filename:
            return False
        if  self.timestamp != value.timestamp:            
            return False
        if  self.filetype != value.filetype:
            return False
        if  self.aanvraag_id != value.aanvraag_id:
            return False
        return True

class FileInfos:
    def __init__(self, aanvraag_id=EMPTY_ID):
        self.aanvraag_id = aanvraag_id
        self.__files = {ft:{'filename': '', 'timestamp':AUTOTIMESTAMP} for ft in FileType if ft != FileType.UNKNOWN}
    def get_filename(self, ft: FileType)->str:
        return self.__files[ft]['filename']
    def set_filename(self, ft: FileType, value: str):
        self.__files[ft]['filename'] = value
    def get_timestamp(self, ft: FileType)->datetime.datetime:
        return self.__files[ft]['timestamp']
    def set_timestamp(self, ft: FileType, value:datetime.datetime):
        self.__files[ft]['timestamp'] = value
    def get_info(self, ft: FileType)->FileInfo:
        return FileInfo(filename=self.get_filename(ft), timestamp=self.get_timestamp(ft), filetype=ft, aanvraag_id=self.aanvraag_id)
    def set_info(self, fi: FileInfo):
        if fi.filetype != FileType.UNKNOWN:
            self.set_filename(fi.filetype, fi.filename)
            self.set_timestamp(fi.filetype, fi.timestamp)
    def reset_info(self, ft: FileType):
        self.set_info(FileInfo('', AUTOTIMESTAMP, ft))
    def reset(self):
        for ft in FileType:
            if ft != FileType.UNKNOWN:
                self.reset_info(ft)


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
    READY_IMPORTED  = 5
    def __str__(self):
        STRS = {AanvraagStatus.INITIAL: 'ontvangen',  AanvraagStatus.NEEDS_GRADING: 'te beoordelen', AanvraagStatus.GRADED: 'beoordeeld', AanvraagStatus.MAIL_READY: 'mail klaar voor verzending', AanvraagStatus.READY: 'verwerkt', AanvraagStatus.READY_IMPORTED: 'verwerkt (ingelezen via Excel)'}
        return STRS[self]
        
class AanvraagBeoordeling(Enum):
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
    def __init__(self, student: StudentInfo, bedrijf: Bedrijf = None, datum_str='', titel='', source_info: FileInfo = None, beoordeling=AanvraagBeoordeling.TE_BEOORDELEN, status=AanvraagStatus.INITIAL, id=EMPTY_ID, aanvraag_nr = 1):        
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
        return FileInfo.timestamp_to_str(self.timestamp)
    def aanvraag_source_file_path(self):
        return Path(self.files.get_filename(FileType.AANVRAAG_PDF))
    def __str__(self):
        versie_str = '' if self.aanvraag_nr == 1 else f'({self.aanvraag_nr})'
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
