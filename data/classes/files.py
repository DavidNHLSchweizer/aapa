from __future__ import annotations
import datetime
from enum import IntEnum
from pathlib import Path
from typing import Iterable
from database.dbConst import EMPTY_ID

from general.filehash import hash_file_digest
from general.fileutil import summary_string
from general.log import log_debug
from general.timeutil import TSC

class File:
    AUTODIGEST = ''
    class Type(IntEnum):
        # INVALID_DOCX        = -3
        INVALID_PDF         = -2
        UNKNOWN             = -1
        AANVRAAG_PDF        = 0
        GRADE_FORM_DOCX     = 1
        COPIED_PDF          = 2
        DIFFERENCE_HTML     = 3
        GRADE_FORM_PDF      = 5
        # GRADE_FORM_EX1_DOCX = 6
        # GRADE_FORM_EX2_DOCX = 7
        # GRADE_FORM_EX3_DOCX = 8
        def __str__(self):
            STR_DICT = {File.Type.UNKNOWN: '?', 
                        File.Type.AANVRAAG_PDF: 'PDF-file (aanvraag)',  
                        File.Type.GRADE_FORM_DOCX: 'Beoordelingsformulier', 
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
    def __init__(self, filename: str, timestamp: datetime.datetime = TSC.AUTOTIMESTAMP, digest = AUTODIGEST, filetype=Type.UNKNOWN, id=EMPTY_ID, aanvraag_id=EMPTY_ID):
        self.id = id
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
    def is_empty(self)->bool:
        return self.filename==''
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
    
class EmptyFile(File):
    def __init__(self, filetype: File.Type):
        super().__init__(filename='', timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, filetype=filetype)

class Files:
    def __init__(self, aanvraag_id=EMPTY_ID):
        self.aanvraag_id = aanvraag_id
        self.__files = {ft:{'id': EMPTY_ID, 'filename': '', 'timestamp':TSC.AUTOTIMESTAMP, 'digest':File.AUTODIGEST} for ft in File.Type if ft != File.Type.UNKNOWN}
    def get_id(self, ft: File.Type)->int:
        return self.__files[ft]['id']
    def set_id(self, ft: File.Type, value: int):
        self.__files[ft]['id'] = value
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
    def get_files(self, skip_empty=True)->Iterable[File]:
        result = []
        for ft in File.Type:
            if (file:=self.get_file(ft)) and (not skip_empty or not file.is_empty()):
                result.append(file)
        return result
    def get_file(self, ft: File.Type)->File:
        if ft == File.Type.UNKNOWN:
            return None
        else:
            return File(id=self.get_id(ft), filename=self.get_filename(ft), timestamp=self.get_timestamp(ft), 
                        digest=self.get_digest(ft), filetype=ft, aanvraag_id=self.aanvraag_id)
    def set_file(self, file: File):
        if file.filetype != File.Type.UNKNOWN:
            self.set_filename(file.filetype, file.filename)
            self.set_timestamp(file.filetype, file.timestamp)
            self.set_digest(file.filetype, file.digest)
            self.set_id(file.filetype, file.id)
    def reset_file(self, file_type: File.Type | set[File.Type]):
        if isinstance(file_type, set):
            for ft in file_type:
                self.set_file(EmptyFile(ft))
        else:
            self.set_file(EmptyFile(file_type))
    def reset(self):
        self.reset_file({ft for ft in File.Type if ft != File.Type.UNKNOWN})
    def get_filetypes(self)->Iterable[File.Type]:
        result = []
        for ft in File.Type:
            if ft != File.Type.UNKNOWN and self.get_filename(ft):
                result.append(ft)
        return result
    def set_files(self, files: Iterable[File]):
        for file in files:
            self.set_file(file)
    def summary(self)->str:
        return "\n".join([f'{file.summary()}' for file in self.get_files(skip_empty=True)])
