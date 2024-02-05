from __future__ import annotations
import datetime
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.base_dirs import BaseDir
from data.classes.const import MijlpaalType
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalBase
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.log import log_warning


class StudentDirectoryAggregator(Aggregator):
    def __init__(self, owner: StudentDirectory):
        super().__init__(owner=owner)
        self.add_class(MijlpaalDirectory, 'directories')
    
class StudentDirectory(AAPAclass):
    def __init__(self, student: Student, directory: str, base_dir: BaseDir = None, id: int = EMPTY_ID):
        super().__init__(id)        
        self.student = student
        self.directory = directory
        self.base_dir = base_dir       
        self._data = StudentDirectoryAggregator(self)
    @property
    def data(self)->Aggregator:
        return self._data
    @property
    def directories(self)->list[MijlpaalDirectory]:
        return self._data.as_list('directories')    
    def get_directories(self, mijlpaal_type: MijlpaalType, sorted=True)->list[MijlpaalDirectory]:
        result = [dir for dir in self.directories if dir.mijlpaal_type == mijlpaal_type]
        if sorted:
            result.sort(key=lambda mpd: (mpd.mijlpaal_type,mpd.datum))
        return result
    def get_directory(self, datum: datetime.datetime, mijlpaal_type: MijlpaalType)->MijlpaalDirectory:
        for directory in self.get_directories(mijlpaal_type):
            if directory.datum==datum:
                return directory
        return None
    def get_files(self)->list[File]:
        result = []
        for directory in self.directories:
            result.extend(directory.files_list)
        return result
    def add(self, mijlpaal: MijlpaalBase):
        if self.get_directory(mijlpaal.datum, mijlpaal.mijlpaal_type):
            log_warning(f'Directory {mijlpaal} is al aanwezig. Wordt overgeslagen.')
            return
        self._data.add(mijlpaal)
    def __str__(self)->str:
        result = f'Student directory voor {str(self.student)}\n\t{self.directory}'
        dir_str = "\n\t".join(str(directory) for directory in self.directories)
        if dir_str:
            result = result + '\n\t' + dir_str 
        return result
    def __eq__(self, value2: StudentDirectory)->bool:
        if not value2:
            return False
        if self.student != value2.student:
            return False
        if self.directory != value2.directory:
            return False        
        if self.base_dir != value2.base_dir:
            return False
        if not self._data.is_equal(value2._data):
            return False
        return True
    

    