from __future__ import annotations
import datetime
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator

from data.general.const import MijlpaalType
from data.classes.mijlpaal_base import MijlpaalBase, MijlpaalGradeable
from database.classes.dbConst import EMPTY_ID
from general.obsolete import obsolete_exception
from general.timeutil import TSC
from main.config import config

class MijlpaalDirectoryAggregator(Aggregator):
    def __init__(self, owner: AAPAclass):
        super().__init__(owner=owner)
        # self.add_class(File, 'files') # to be deleted later
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(Verslag, 'verslagen')
    def find_filename(self,filename: str):
        obsolete_exception('find_filename')
    def find_mijlpaal(self, mijlpaal: MijlpaalGradeable)->MijlpaalGradeable:
        for mijlpaal2 in self.as_class_list(mijlpaal):
            if mijlpaal2 == mijlpaal:
                return mijlpaal2
        return None        
    def find_mijlpaal_id(self, mijlpaal: MijlpaalGradeable)->MijlpaalGradeable:
        for mijlpaal2 in self.as_class_list(mijlpaal):
            if mijlpaal2.id == mijlpaal.id:
                return mijlpaal2
        return None            
    def get_files(self)->list[File]:
        result = []
        for class_type in self.class_types():
            for mijlpaal in self.as_list(class_type):
                result.extend(mijlpaal.files_list)
        return result
    
class MijlpaalDirectory(MijlpaalBase):    
    def __init__(self, mijlpaal_type: MijlpaalType, directory: str, datum: datetime.datetime, kans=0, id=EMPTY_ID):
        super().__init__(mijlpaal_type=mijlpaal_type, datum=datum, kans=kans, id=id)
        self.directory = directory
        self.mijlpalen = MijlpaalDirectoryAggregator(self)
    def get_files(self)->list[File]: 
        return self.mijlpalen.get_files()
    @property
    def items(self)->list[MijlpaalGradeable]:
        result = self.mijlpalen.as_list('aanvragen')
        result.extend(self.mijlpalen.as_list('verslagen'))
        return result        
    @property
    def nr_items(self):
        return self.mijlpalen.nr_items('aanvragen') + self.mijlpalen.nr_items('verslagen')
    def aanvragen(self)->list[Aanvraag]: return self.mijlpalen.as_list('aanvragen')
    @property
    def nr_aanvragen(self):
        return self.mijlpalen.nr_items('aanvragen')
    @property
    def verslagen(self)->list[Verslag]: return self.mijlpalen.as_list('verslagen')
    @property
    def nr_verslagen(self):
        return self.mijlpalen.nr_items('verslagen')
    # @property
    # def files_list(self)->list[File]: 
    #     obsolete_exception('files_list in mijlpaaldirectory')
    @property
    def nr_items(self):
        return self.nr_aanvragen + self.nr_verslagen
    # def _find_file(self, file: File)->File:
    #     obsolete_exception('_find_file in mijlpaaldirectory')        
    # def register_file(self, filename: str, filetype: File.Type, mijlpaal_type: MijlpaalType)->File:
    #     obsolete_exception('register_file in mijlpaaldirectory')
    def register_mijlpaal(self, mijlpaal: MijlpaalGradeable)->MijlpaalGradeable:
        if self.mijlpalen.contains_id(mijlpaal):
            return self.mijlpalen.find_mijlpaal_id(mijlpaal)
        elif self.mijlpalen.contains(mijlpaal):
            return self.mijlpalen.find_mijlpaal(mijlpaal)
        else:
            self.mijlpalen.add(mijlpaal)
            return mijlpaal
    def relevant_attributes(self) -> set[str]:
        return super().relevant_attributes() | {'directory'}
    def equal_relevant_attributes(self, value: MijlpaalGradeable)->bool:
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
        file_str = "\n\t\t".join([file.summary(name_only=True) for file in self.get_files()])
        if file_str:
            s = s + "\n\t\t"+ file_str
        return s
    def __eq__(self, value2: MijlpaalGradeable)->bool:
        if not super().__eq__(value2):
            return False
        if self.directory != value2.directory:
            return False
        if self.mijlpalen != value2.mijlpalen:
            return False
        return True
    def __gt__(self, value2: MijlpaalGradeable)->bool:
        return value2 is not None and self.directory > value2.directory
    @staticmethod
    def directory_name(mijlpaal_type: MijlpaalType, datum: datetime.datetime)->str:
        beoordelen = ' Beoordelen' if not mijlpaal_type  in [MijlpaalType.PRODUCT_BEOORDELING, MijlpaalType.EINDBEOORDELING, MijlpaalType.AFSTUDEERZITTING] else ""
        return f'{datetime.datetime.strftime(datum, "%Y-%m-%d")}{beoordelen} {str(mijlpaal_type).title()}'