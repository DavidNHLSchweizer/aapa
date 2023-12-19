from __future__ import annotations
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.base_dirs import BaseDir
from data.classes.mijlpaal_base import MijlpaalBase
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID


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
    def add(self, mijlpaal: MijlpaalBase):
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