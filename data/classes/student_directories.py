from __future__ import annotations
from ast import Tuple
import datetime
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.classes.base_dirs import BaseDir
from data.general.const import MijlpaalType, StudentDirectoryStatus
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalBase
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from database.classes.dbConst import EMPTY_ID
from general.timeutil import TSC
from main.log import log_warning


class StudentDirectoryAggregator(Aggregator):
    def __init__(self, owner: StudentDirectory):
        super().__init__(owner=owner)
        self.add_class(MijlpaalDirectory, 'directories')
    def contains(self, mp_dir: MijlpaalDirectory)->bool:
        for dir in self.as_list('directories'):
            if dir.id == mp_dir.id:
                return True
        return False
    
class StudentDirectory(AAPAclass):
    Status = StudentDirectoryStatus
    def __init__(self, student: Student, directory: str, base_dir: BaseDir = None, status=Status.UNKNOWN, id: int = EMPTY_ID):
        super().__init__(id)        
        self.student = student
        self.directory = directory
        self.base_dir = base_dir   
        self.status  = status    
        self._data = StudentDirectoryAggregator(self)
    @property
    def data(self)->Aggregator:
        return self._data
    @property
    def directories(self)->list[MijlpaalDirectory]:
        return self._data.as_list('directories')    
    def get_directories(self, mijlpaal_type: MijlpaalType, sorted=True)->list[MijlpaalDirectory]:
        def get_key(mpd: MijlpaalDirectory)->Tuple[MijlpaalType,datetime.datetime]:
            # some mpd's have a "zero" datum, workaround for this
            return (mpd.mijlpaal_type, mpd.datum if isinstance(mpd.datum,datetime.datetime) else datetime.datetime(2000,1,1))
        result = [dir for dir in self.directories if dir.mijlpaal_type == mijlpaal_type]
        if sorted:
            result.sort(key=get_key)
        return result
    def get_directory(self, datum: datetime.datetime, mijlpaal_type: MijlpaalType)->MijlpaalDirectory:
        for directory in self.get_directories(mijlpaal_type):
            #er is maar 1 aanvraag directory, de datum is niet wezenlijk van belang daarvoor
            #voor andere mijlpalen (verslagen) juist wel, maar niet tot in de milliseconden. 
            if mijlpaal_type == MijlpaalType.AANVRAAG or TSC.round_to_day(directory.datum)==TSC.round_to_day(datum):
                return directory
        return None
    def get_files(self)->list[File]:
        result = []
        for directory in self.directories:
            result.extend(directory.files_list)
        return result
    def get_file_directory(self, file: File)->MijlpaalDirectory:
        for directory in self.directories:
            if file in directory.files_list:
                return directory
        return None
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
    

    