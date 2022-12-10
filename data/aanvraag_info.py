from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum
from pathlib import Path
import re
from database.dbConst import EMPTY_ID
from general.date_parser import DateParser


def is_valid_email(email: str)->bool:
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.compile(email_regex).match(email) is not None

@dataclass
class Bedrijf:        
    bedrijfsnaam: str = ''
    id: int = EMPTY_ID
    def __str__(self): 
        return f'{self.id}:{self.bedrijfsnaam}'
    def valid(self):
        return self.bedrijfsnaam != ''

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

class FileInfo:
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    def __init__(self, filename: str, timestamp: datetime.datetime, filetype: FileType):
        self.filename = filename
        self.timestamp = timestamp
        self.filetype = filetype
    def __str__(self): 
        return f'{self.filename}: {str(self.filetype)} [{FileInfo.timestamp_to_str(self.timestamp)}]'    
    @property    
    def timestamp(self):
        return self._timestamp
    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = self.__rounded_timestamp(value)
    def __rounded_timestamp(self, value):
        #remove possible milliseconds so that the string can be read uniformly from the database if needed
        return FileInfo.str_to_timestamp(FileInfo.timestamp_to_str(value))
    @staticmethod
    def timestamp_to_str(value):
        return datetime.datetime.strftime(value, FileInfo.DATETIME_FORMAT)
    @staticmethod
    def str_to_timestamp(value):
        return datetime.datetime.strptime(value, FileInfo.DATETIME_FORMAT)

class StudentInfo:
    def __init__(self, student_name='', studnr='', telno='', email=''):        
        self.student_name = student_name
        self.studnr = studnr
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

class AanvraagDocumentInfo:
    def __init__(self, fileinfo: FileInfo, student: StudentInfo, bedrijf: Bedrijf = None, datum_str='', titel='', beoordeling=0):        
        self._dateparser = DateParser()
        self.fileinfo = fileinfo
        self.student = student
        self.bedrijf = bedrijf
        print(datum_str)
        self.datum_str = datum_str
        self.titel = titel
        self.beoordeling = beoordeling        
    def __str__(self):
        s = f'{str(self.student)} - {self.datum_str}: {self.bedrijf.bedrijfsnaam} - "{self.titel}"'
        if self.beoordeling > 0:
            s = s + ' (voldoende)'
        return s
    def __eq__(self, value: AanvraagDocumentInfo):
        self_date,_ = self._dateparser.parse_date(self.datum_str)
        value_date,_= self._dateparser.parse_date(self.datum_str)
        if self_date  != value_date:
            return False
        if  self.datum != value.datum:
            return False
        if  self.versie != value.versie:
            return False
        if  self.student != value.student:
            return False
        if  self.bedrijf != value.bedrijf:
            return False
        if  self.titel != value.titel:
            return False
        return True
    def valid(self):
        return self.student.valid() and self.bedrijf.valid()
    @property
    def datum(self): 
        return self.__datum
    @property
    def versie(self):
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

class AanvraagInfo:
    def __init__(self, docInfo: AanvraagDocumentInfo, timestamp = datetime.datetime.now(), passed = False, sequence=1):
        self.docInfo = docInfo
        self.timestamp = timestamp
        self.passed = passed
        self.key = f'{self.docInfo.studnr}|{sequence}'
    def modify(self, **kwdargs):
        for kwd,value in kwdargs.items():
            setattr(self, kwd, value)
    def __str__(self):
        result = f'{str(self.docInfo)} [{self.timestamp}] ({self.key})'
        if self.passed:
            result = result + ' (voldoende)'
        return result
    def __eq__(self, value: AanvraagInfo)->bool:
        if self.timestamp != value.timestamp:
            return False
        if self.passed != value.passed:
            return False
        if not (self.docInfo == value.docInfo):
            return False
        return True      
    def valid(self):
        return self.docInfo.valid() and isinstance(self.timestamp, datetime.datetime)

