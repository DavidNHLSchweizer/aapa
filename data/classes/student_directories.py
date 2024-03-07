from __future__ import annotations
from ast import Tuple
import datetime
from enum import Enum, auto
from pathlib import Path
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
    def __str__(self)->str:
        return "\n".join([str(d) for d in self.as_list('directories')])
    def contains(self, mp_dir: MijlpaalDirectory)->bool:
        for dir in self.as_list('directories'):
            if dir.id == mp_dir.id:
                return True
        return False
    def _find(self, value: MijlpaalDirectory)->MijlpaalDirectory:
        """ Returns mijlpaaldirectory with the same name.

            Note: search is case-insensitive, since there is a bit of inconsistency in the real world 
            and Windows-paths are case-insensitive anyway.

        """
        for mp_dir in self.as_list('directories'):
            if str(mp_dir.directory).lower() == str(value.directory.lower()):
                return mp_dir 
        return None
SDA = StudentDirectoryAggregator
    
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
    def data(self)->SDA:
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
    def get_directory(self, datum: datetime.datetime, mijlpaal_type: MijlpaalType, error_margin = 0.0)->MijlpaalDirectory:
        """ Geeft mijlpaal_directory voor dit mijlpaal_type en deze datum

            voor aanvragen is er 1 aanvraag directory, de datum is niet wezenlijk van belang daarvoor

            voor andere mijlpalen (verslagen) juist wel, maar niet tot in de milliseconden. 
            De praktijk is ook dat er soms al een directory is die bv 1 dag afwijkt. Vandaar error_margin.
            
            parameters
            ----------
            datum: De datum waarop naar een mijlpaaldirectory wordt gezocht. Waarschijnlijk de timestamp van een file  die geplaatst moet worden 
            mijlpaal_type: De soort mijlpaal
            error_margin: range van dagen waarin gezocht wordt. Als er een mijlpaaldirectory bestaat waarvan de timestamp tussen 
            datum-error_margin/2 en datum+error_margin/2 ligt wordt deze teruggegeven.

            returns
            -------
            de mijlpaaldirectory waarbij deze datum/mijlpaal_type hoort.
            None als er nog geen bestaat.

        """
        for directory in self.get_directories(mijlpaal_type):
            new_date = TSC.round_to_day(datum)
            if mijlpaal_type == MijlpaalType.AANVRAAG or TSC.equal_in_range(directory.datum, new_date, error_margin):
                return directory
        return None
    def get_files(self)->list[File]:
        result = []
        for directory in self.directories:
            result.extend(directory.get_files())
        return result
    def get_file_directory(self, file: File)->MijlpaalDirectory:
        for directory in self.directories:
            if file in directory.get_files():
                return directory
        return None
    def get_filename_directory(self, filename: str)->MijlpaalDirectory:
        directory = str(Path(filename).parent).lower()
        for mp_dir in self.directories:
            if str(mp_dir.directory).lower() == directory:
                return mp_dir
        return None
    def add(self, mijlpaal: MijlpaalBase):
        if self.get_directory(mijlpaal.datum, mijlpaal.mijlpaal_type):
            log_warning(f'Directory {mijlpaal} is al aanwezig. Wordt overgeslagen.')
            return
        self._data.add(mijlpaal)
    def summary(self)->str:
        return f'Student directory voor {str(self.student)}\n\t{File.display_file(self.directory)}'
    def __str__(self)->str:
        result = self.summary()
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
    

    