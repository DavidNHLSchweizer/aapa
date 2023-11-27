from __future__ import annotations 
from copy import copy
import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from database.dbConst import EMPTY_ID
from general.filehash import hash_file_digest
from general.fileutil import summary_string
from general.timeutil import TSC

class FilesException(Exception): pass
class File(AAPAclass):
    AUTODIGEST = ''
    class Type(IntEnum):
        INVALID_DOCX        = -3
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
        def is_invalid(filetype: File.Type)->bool:
            return filetype in {File.Type.INVALID_PDF, File.Type.INVALID_DOCX}

    @staticmethod
    def get_timestamp(filename: str)-> datetime.datetime:
        return TSC.rounded_timestamp(datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime))
    @staticmethod
    def get_digest(filename: str)->str:
        return hash_file_digest(filename)
    def __init__(self, filename: str, timestamp: datetime.datetime = TSC.AUTOTIMESTAMP, digest = AUTODIGEST, filetype=Type.UNKNOWN, id=EMPTY_ID, aanvraag_id=EMPTY_ID):
        super().__init__(id)
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
    def timestamp(self): return self._timestamp
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
    
class Files(Aggregator):
    def __init__(self, owner: AAPAclass, file_types:set[File.Type] = {ft for ft in File.Type if ft != File.Type.UNKNOWN}):
        super().__init__(owner=owner)
        self.file_types = file_types
        self.add_class(File, 'files')
    def add(self, file:File):
        if not file.filetype in self.file_types:
            raise FilesException(f'Invalid File:{file}')
        super().add(file)
    @property
    def files(self)->list[File]:
        return self.as_list('files')
    def _remove_filetype(self, ft: File.Type):
        if file := self._get(ft):
            self.remove(file)
    def _get(self, ft: File.Type)->File:
        for file in self.files:
            if file.filetype == ft:
                return file
        return None
    def __get_attr(self, ft: File.Type, attr_name: str, default: Any)->Any:
        if file := self._get(ft):
            return getattr(file, attr_name)
        return default
    def __set_attr(self, ft: File.Type, attr_name: str, value: Any):
        if file := self._get(ft):
            setattr(file, attr_name, value)
    def get_filename(self, ft: File.Type)->str:
        return self.__get_attr(ft, 'filename', '')
    def get_timestamp(self, ft: File.Type)->datetime.datetime:
        return self.__get_attr(ft, 'timestamp', TSC.AUTOTIMESTAMP)
    def get_digest(self, ft: File.Type)->str:
        return self.__get_attr(ft, 'digest',File.AUTODIGEST)
    def get_file(self, ft: File.Type)->File:
        if ft != File.Type.UNKNOWN and (file := self._get(ft)):
            return copy(file)
        return None
    def set_file(self, file: File):
        if file.filetype == File.Type.UNKNOWN or not file.filetype in self.file_types:
            return
        if current := self._get(file.filetype):
            self.remove(current)
        self.add(copy(file))
    def reset_file(self, file_type: File.Type | set[File.Type]):
        if isinstance(file_type, set):
            all_file_types = [file.filetype for file in self.files if file.filetype in file_type]
        else:
            all_file_types = [file_type]                 
        for ft in all_file_types:
            self._remove_filetype(ft)
    def reset(self):
        self.reset_file({ft for ft in File.Type if ft != File.Type.UNKNOWN})
    def get_filetypes(self)->Iterable[File.Type]:
        return [file.type for file in self.files]
    def set_files(self, files: Iterable[File]):
        for file in files:
            self.set_file(file)
    def summary(self)->str:
        return "\n".join([f'{file.summary()}' for file in self.files])
