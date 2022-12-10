from dataclasses import dataclass
import datetime
from enum import Enum


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

@dataclass
class FileInfo:
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    filename:str = '' 
    timestamp: datetime.datetime = None
    filetype: FileType = FileType.UNKNOWN
    def __str__(self): 
        return f'{self.filename}: {str(self.filetype)} [{FileInfo.timestamp_to_str(self.timestamp)}]'
    @staticmethod
    def timestamp_to_str(value):
        return datetime.datetime.strftime(value, FileInfo.DATETIME_FORMAT)
    @staticmethod
    def str_to_timestamp(value):
        return datetime.datetime.strptime(value, FileInfo.DATETIME_FORMAT)


fi = FileInfo('jezusredt.docx', datetime.datetime.now(), FileType.OORDEEL_DOCX)
print(fi)
fi2 = FileInfo('jezusredt.pdf', FileInfo.str_to_timestamp(FileInfo.timestamp_to_str(fi.timestamp)), FileType.OORDEEL_PDF)
print(fi2)