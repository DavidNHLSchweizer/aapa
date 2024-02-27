from __future__ import annotations
import datetime
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator

from data.general.const import MijlpaalType
from data.classes.mijlpaal_base import MijlpaalBase
from database.classes.dbConst import EMPTY_ID
from general.timeutil import TSC
from main.config import config

class MijlpaalDirectoryAggregator(Aggregator):
    def __init__(self, owner: AAPAclass):
        super().__init__(owner=owner)
        self.add_class(File, 'files') # to be deleted later
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(Verslag, 'verslagen')
    def find_filename(self,filename: str):
        for file in self.as_list('files'):
            if str(file.filename) == filename:
                return file
        return None        
    
class MijlpaalDirectory(MijlpaalBase):    
    def __init__(self, mijlpaal_type: MijlpaalType, directory: str, datum: datetime.datetime, kans=0, id=EMPTY_ID):
        super().__init__(mijlpaal_type=mijlpaal_type, datum=datum, kans=kans, id=id)
        self.directory = directory
        self.mijlpalen = MijlpaalDirectoryAggregator(self)
    @property
    def files_list(self)->list[File]: return self.mijlpalen.as_list('files')
    # @property
    # def files(self)->list[File]:
    #     raise Exception('call to MijlpaalDirectory.files, function deprecated.')
    @property
    def nr_files(self):
        return self.mijlpalen.nr_items('files')
    def _find_file(self, file: File)->File:
        return self.mijlpalen.find_filename(file.filename)
    def register_file(self, filename: str, filetype: File.Type, mijlpaal_type: MijlpaalType)->File:
        result = File(filename=filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, mijlpaal_type=mijlpaal_type)
        if self.mijlpalen.contains(result):
            return self.mijlpalen.find_filename(filename)
        else:
            self.mijlpalen.add(result)
        return result    
    def relevant_attributes(self) -> set[str]:
        return super().relevant_attributes() | {'directory'}
    def equal_relevant_attributes(self, value: MijlpaalDirectory)->bool:
        if  str(self.directory).lower() != str(value.directory).lower():
            return False        
        if  self.mijlpaal_type != value.mijlpaal_type:            
            return False
        return True
    def ensure_datum(self):
        if self.datum == TSC.AUTOTIMESTAMP:
            self.datum = File.get_timestamp(self.directory)
    def summary(self)->str:
        return f'{File.display_file(self.directory)} [{self.mijlpaal_type}] {TSC.timestamp_to_str(self.datum)}'
    def __str__(self):        
        s = self.summary()
        if self.kans > 0:
            s = f'{s} (kans: {self.kans})'
        file_str = "\n\t\t".join([file.summary(name_only=True) for file in self.files_list])
        if file_str:
            s = s + "\n\t\t"+ file_str
        return s
    def __eq__(self, value2: MijlpaalDirectory)->bool:
        if not super().__eq__(value2):
            return False
        if self.directory != value2.directory:
            return False
        return True
    def __gt__(self, value2: MijlpaalDirectory)->bool:
        return value2 is not None and self.directory > value2.directory
    @staticmethod
    def directory_name(mijlpaal_type: MijlpaalType, datum: datetime.datetime)->str:
        beoordelen = ' Beoordelen' if not mijlpaal_type  in [MijlpaalType.PRODUCT_BEOORDELING, MijlpaalType.EINDBEOORDELING, MijlpaalType.AFSTUDEERZITTING] else ""
        return f'{datetime.datetime.strftime(datum, "%Y-%m-%d")}{beoordelen} {str(mijlpaal_type).title()}'