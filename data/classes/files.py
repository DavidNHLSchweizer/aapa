from __future__ import annotations 
import datetime
from enum import Enum, auto
from pathlib import Path
import re
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.general.const import FileType, MijlpaalType
from database.classes.dbConst import EMPTY_ID
from general.filehash import hash_file_digest
from general.fileutil import last_parts_file, summary_string
from general.timeutil import TSC

class FilesException(Exception): pass
class File(AAPAclass):
    AUTODIGEST = ''
    Type = FileType
    @staticmethod
    def get_timestamp(filename: str)-> datetime.datetime:
        return TSC.rounded_timestamp(datetime.datetime.fromtimestamp(Path(filename).stat().st_mtime))
    @staticmethod
    def get_digest(filename: str)->str:
        return hash_file_digest(filename)
    @staticmethod
    def display_file(filename: str)->str:
        """ returns shortened filename starting with the year-part of the file (e.g. 2022-2023). """
        def __compute_min_parts(filename: str)->int:
            pattern = re.compile(r'\d{4,4}\-\d{4,4}')
            parts = Path(filename).parts
            for n,part in enumerate(parts):
                if pattern.match(part):
                    return len(parts)-n
            return 3
        return last_parts_file(filename,__compute_min_parts(filename))
    def __init__(self, filename: str, timestamp: datetime.datetime = TSC.AUTOTIMESTAMP, digest = AUTODIGEST, 
                 filetype=Type.UNKNOWN, mijlpaal_type = MijlpaalType.UNKNOWN, id=EMPTY_ID):
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
        self.mijlpaal_type = mijlpaal_type
    def __str__(self): 
        return f'{self.filename}: {str(self.filetype)}-{str(self.mijlpaal_type)} [{TSC.timestamp_to_str(self.timestamp)}]'
    def summary(self, len_filename = 72, name_only=False)->str:
        if name_only:
            return f'{Path(self.filename).name}: {str(self.filetype)}-{self.mijlpaal_type} [{TSC.timestamp_to_str(self.timestamp)}]'     
        else:
            return f'{File.display_file(self.filename)}: {str(self.filetype)}-{self.mijlpaal_type} [{TSC.timestamp_to_str(self.timestamp)}]'
    @property    
    def timestamp(self): return self._timestamp
    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = TSC.rounded_timestamp(value)
    def is_empty(self)->bool:
        return self.filename==''
    def relevant_attributes(self)->set[str]:
        return {'filename', 'timestamp', 'digest'}
    def ensure_timestamp_and_digest(self):
        if self.timestamp == TSC.AUTOTIMESTAMP:
            self.timestamp = File.get_timestamp(self.filename)
        if self.digest == File.AUTODIGEST:
            self.digest = File.get_digest(self.filename)
    def equal_relevant_attributes(self, value: File)->bool:
        if  self.filename != value.filename:
            return False
        if  self.timestamp != value.timestamp:            
            return False
        if  self.digest != value.digest:            
            return False
        return True
    def __eq__(self, value: File):
        if  self.filename != value.filename:
            return False
        if  self.timestamp != value.timestamp:            
            return False
        if  self.digest != value.digest:            
            return False
        if  self.filetype != value.filetype:
            return False
        if  self.mijlpaal_type != value.mijlpaal_type:
            return False
        return True
    def __gt__(self, value2: File)->bool:
        return value2 is not None and self.filename > value2.filename
    
class Files(Aggregator):
    def __init__(self, owner: AAPAclass, allow_multiple = True):
        super().__init__(owner=owner)
        self.allow_multiple = allow_multiple
        self.add_class(File, 'files')
    def add(self, files:File|list[File]):
        if not self.allow_multiple:
            if isinstance(files, list):
                for filetype in {file.filetype for file in files}:
                    self.remove_filetype(filetype)
            else:
                self.remove_filetype(files.filetype)
        super().add(files)
    @property
    def files(self)->list[File]:
        return self.as_list('files', sort_key=lambda file: file.filetype)
    def nr_files(self, filetypes: set[File.Type] = {filetype for filetype in File.Type}):
        result = 0
        for file in self.files:
            if file.filetype in filetypes:
                result += 1
        return result
    def remove_filetype(self, ft: File.Type):
        if file := self.get_file(ft):
            self.remove(file)
    def get_file(self, ft: File.Type)->File:
        for file in self.files:
            if file.filetype == ft:
                return file
        return None
    def get_filename(self, ft: File.Type)->File | list[File]:
        if file := self.get_file(ft):
            return file.filename
        return ''
    def get_timestamp(self, ft: File.Type)->datetime.datetime:
        if file := self.get_file(ft):
            return file.timestamp
        return ''
    def get_digest(self, ft: File.Type)->str:
        if file := self.get_file(ft):
            return file.digest
        return ''
    def summary(self)->str:
        return "\n".join([f'{file.summary()}' for file in self.files])
    def _find(self, value: File)->File:
        for file in self.files:
            if str(file.filename) == str(value.filename):
                return file 
        return None
    