from __future__ import annotations
import datetime
from enum import Enum, auto
from data.classes.files import File

from data.general.const import MijlpaalType
from data.classes.mijlpaal_base import MijlpaalBase
from database.classes.dbConst import EMPTY_ID
from general.timeutil import TSC

class MijlpaalDirectory(MijlpaalBase):    
    class DIFF(Enum):
        MIJLPAAL    = auto()
        KANS        = auto()
        DIRECTORY   = auto()
        DATUM       = auto()
        FILES       = auto()
    def __init__(self, mijlpaal_type: MijlpaalType, directory: str, datum: datetime.datetime, kans=0, id=EMPTY_ID):
        super().__init__(mijlpaal_type=mijlpaal_type, datum=datum, kans=kans, id=id)
        self.directory = directory
    def relevant_attributes(self) -> set[str]:
        return super().relevant_attributes() | {'directory'}
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
    def difference(self, value2: MijlpaalDirectory)->dict:
        result = {}
        # if self.mijlpaal_type != value2.mijlpaal_type:
        #     result[MijlpaalDirectory.DIFF.MIJLPAAL] = value2.mijlpaal_type
        # if self.kans != value2.kans:
        #     result[MijlpaalDirectory.DIFF.KANS] = value2.kans
        if self.directory != value2.directory:
            result[MijlpaalDirectory.DIFF.DIRECTORY] = value2.directory
        # if self.datum != value2.datum:
        #     result[MijlpaalDirectory.DIFF.DATUM] = value2.datum
        if (diff_files := self.files.difference(value2.files)):
            result[MijlpaalDirectory.DIFF.FILES] = diff_files
        return result
    @staticmethod
    def directory_name(mijlpaal_type: MijlpaalType, datum: datetime.datetime)->str:
        beoordelen = ' Beoordelen' if not mijlpaal_type  in [MijlpaalType.PRODUCT_BEOORDELING, MijlpaalType.EINDBEOORDELING, MijlpaalType.AFSTUDEERZITTING] else ""
        return f'{datetime.datetime.strftime(datum, "%Y-%m-%d")}{beoordelen} {str(mijlpaal_type).title()}'