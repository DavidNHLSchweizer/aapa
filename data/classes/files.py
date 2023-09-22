from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from database.dbConst import EMPTY_ID

from general.filehash import hash_file_digest
from general.fileutil import summary_string
from general.timeutil import TSC

AUTODIGEST = ''
class FileType(IntEnum):
    UNKNOWN             = -1
    AANVRAAG_PDF        = 0
    INVALID_PDF         = 1
    TO_BE_GRADED_DOCX   = 2
    GRADED_DOCX         = 3
    GRADED_PDF          = 4
    COPIED_PDF          = 5
    DIFFERENCE_HTML     = 6
    def __str__(self):
        STR_DICT = {FileType.UNKNOWN: '?', FileType.AANVRAAG_PDF: 'PDF-file (aanvraag)',  
                    FileType.TO_BE_GRADED_DOCX: 'Formulier beoordeling (Word format)', FileType.GRADED_DOCX: 'Ingevuld formulier beoordeling (Word format)', 
                    FileType.GRADED_PDF: 'Ingevuld formulier beoordeling (PDF format)', FileType.COPIED_PDF: 'Kopie van PDF-file (aanvraag)',
                    FileType.DIFFERENCE_HTML: 'verschilbestand met vorige versie aanvraag'
                    }
        return STR_DICT.get(self, '!unknown')

class FileInfo:
    @staticmethod
    def get_timestamp(filename: str)-> datetime.datetime:
        return TSC.rounded_timestamp(datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime))
    @staticmethod
    def get_digest(filename: str)->str:
        return hash_file_digest(filename)
    def __init__(self, filename: str, timestamp: datetime.datetime = TSC.AUTOTIMESTAMP, digest = AUTODIGEST, filetype: FileType=FileType.UNKNOWN, aanvraag_id=EMPTY_ID):
        self.filename = str(filename) # to remove the WindowsPath label if needed
        if Path(filename).is_file():
            if timestamp == TSC.AUTOTIMESTAMP:
                self.timestamp = FileInfo.get_timestamp(filename)
            else:
                self.timestamp = timestamp
            if digest == AUTODIGEST:
                self.digest = FileInfo.get_digest(filename)
            else:
                self.digest = digest
        else:
            self.timestamp=timestamp
            self.digest=digest
        self.filetype = filetype
        self.aanvraag_id = aanvraag_id
    def __str__(self): 
        return f'{self.filename}: {str(self.filetype)} [{TSC.timestamp_to_str(self.timestamp)}]'   
    def summary(self, len_filename = 72)->str:
        return f'{summary_string(self.filename, maxlen=len_filename)}: {str(self.filetype)} [{TSC.timestamp_to_str(self.timestamp)}]'     
    @property    
    def timestamp(self):
        return self._timestamp
    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = TSC.rounded_timestamp(value)
    def __eq__(self, value: FileInfo):
        if  self.filename != value.filename:
            return False
        if  self.timestamp != value.timestamp:            
            return False
        if  self.digest != value.digest:            
            return False
        if  self.filetype != value.filetype:
            return False
        if  self.aanvraag_id != value.aanvraag_id:
            return False
        return True

class FileInfos:
    def __init__(self, aanvraag_id=EMPTY_ID):
        self.aanvraag_id = aanvraag_id
        self.__files = {ft:{'filename': '', 'timestamp':TSC.AUTOTIMESTAMP, 'digest':AUTODIGEST} for ft in FileType if ft != FileType.UNKNOWN}
    def get_filename(self, ft: FileType)->str:
        return self.__files[ft]['filename']
    def set_filename(self, ft: FileType, value: str):
        self.__files[ft]['filename'] = value
    def get_timestamp(self, ft: FileType)->datetime.datetime:
        return self.__files[ft]['timestamp']
    def set_timestamp(self, ft: FileType, value:datetime.datetime):
        self.__files[ft]['timestamp'] = value
    def get_digest(self, ft: FileType)->str:
        return self.__files[ft]['digest']
    def set_digest(self, ft: FileType, value: str):
        self.__files[ft]['digest'] = value
    def get_infos(self)->list[FileInfo]:
        result = []
        for ft in FileType:
            if (info:=self.get_info(ft)):
                result.append(info)
        return result
    def get_info(self, ft: FileType)->FileInfo:
        if ft == FileType.UNKNOWN:
            return None
        else:
            return FileInfo(filename=self.get_filename(ft), timestamp=self.get_timestamp(ft), digest=self.get_digest(ft), filetype=ft, aanvraag_id=self.aanvraag_id)
    def set_info(self, fi: FileInfo):
        if fi.filetype != FileType.UNKNOWN:
            self.set_filename(fi.filetype, fi.filename)
            self.set_timestamp(fi.filetype, fi.timestamp)
            self.set_digest(fi.filetype, fi.digest)
    def reset_info(self, file_type: FileType | set[FileType]):
        if isinstance(file_type, set):
            for ft in file_type:
                self.set_info(FileInfo('', TSC.AUTOTIMESTAMP, '', ft))
        else:
            self.set_info(FileInfo('', TSC.AUTOTIMESTAMP, '', file_type))
    def reset(self):
        self.reset_info({ft for ft in FileType if ft != FileType.UNKNOWN})

