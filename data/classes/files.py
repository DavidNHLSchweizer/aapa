from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from database.dbConst import EMPTY_ID

from general.filehash import hash_file_digest
from general.fileutil import summary_string
from general.timeutil import TSC

class File:
    AUTODIGEST = ''
    class Type(IntEnum):
        INVALID_PDF         = -2
        UNKNOWN             = -1
        AANVRAAG_PDF        = 0
        GRADE_FORM_DOCX     = 1
        COPIED_PDF          = 2
        DIFFERENCE_HTML     = 3
        GRADED_DOCX         = 4
        GRADE_FORM_PDF          = 5
        def __str__(self):
            STR_DICT = {File.Type.UNKNOWN: '?', File.Type.AANVRAAG_PDF: 'PDF-file (aanvraag)',  
                        File.Type.GRADE_FORM_DOCX: 'Beoordelingsformulier', File.Type.GRADED_DOCX: 'Ingevuld beoordelingsformulier', 
                        File.Type.GRADE_FORM_PDF: 'Ingevuld beoordelingsformulier (PDF format)', File.Type.COPIED_PDF: 'Kopie van PDF-file (aanvraag)',
                        File.Type.DIFFERENCE_HTML: 'verschilbestand met vorige versie aanvraag'
                        }
            return STR_DICT.get(self, '!unknown')

    @staticmethod
    def get_timestamp(filename: str)-> datetime.datetime:
        return TSC.rounded_timestamp(datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime))
    @staticmethod
    def get_digest(filename: str)->str:
        return hash_file_digest(filename)
    def __init__(self, filename: str, timestamp: datetime.datetime = TSC.AUTOTIMESTAMP, digest = AUTODIGEST, filetype=Type.UNKNOWN, aanvraag_id=EMPTY_ID):
        self.filename = str(filename) # to remove the WindowsPath label if needed
        if Path(filename).is_file():
            if timestamp == TSC.AUTOTIMESTAMP:
                self.timestamp = File.get_timestamp(filename)
            else:
                self.timestamp = timestamp
            if digest == File.AUTODIGEST:
                self.digest = File.get_digest(filename)
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
    def __eq__(self, value: File):
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

class Files:
    def __init__(self, aanvraag_id=EMPTY_ID):
        self.aanvraag_id = aanvraag_id
        self.__files = {ft:{'filename': '', 'timestamp':TSC.AUTOTIMESTAMP, 'digest':File.AUTODIGEST} for ft in File.Type if ft != File.Type.UNKNOWN}
    def get_filename(self, ft: File.Type)->str:
        return self.__files[ft]['filename']
    def set_filename(self, ft: File.Type, value: str):
        self.__files[ft]['filename'] = value
    def get_timestamp(self, ft: File.Type)->datetime.datetime:
        return self.__files[ft]['timestamp']
    def set_timestamp(self, ft: File.Type, value:datetime.datetime):
        self.__files[ft]['timestamp'] = value
    def get_digest(self, ft: File.Type)->str:
        return self.__files[ft]['digest']
    def set_digest(self, ft: File.Type, value: str):
        self.__files[ft]['digest'] = value
    def get_files(self)->list[File]:
        result = []
        for ft in File.Type:
            if (file:=self.get_file(ft)):
                result.append(file)
        return result
    def get_file(self, ft: File.Type)->File:
        if ft == File.Type.UNKNOWN:
            return None
        else:
            return File(filename=self.get_filename(ft), timestamp=self.get_timestamp(ft), digest=self.get_digest(ft), filetype=ft, aanvraag_id=self.aanvraag_id)
    def set_file(self, file: File):
        if file.filetype != File.Type.UNKNOWN:
            self.set_filename(file.filetype, file.filename)
            self.set_timestamp(file.filetype, file.timestamp)
            self.set_digest(file.filetype, file.digest)
    def reset_file(self, file_type: File.Type | set[File.Type]):
        if isinstance(file_type, set):
            for ft in file_type:
                self.set_file(File('', TSC.AUTOTIMESTAMP, '', ft))
        else:
            self.set_file(File('', TSC.AUTOTIMESTAMP, '', file_type))
    def reset(self):
        self.reset_file({ft for ft in File.Type if ft != File.Type.UNKNOWN})

