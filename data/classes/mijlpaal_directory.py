import datetime
from data.classes.aapa_class import AAPAclass
from data.classes.const import MijlpaalType
from data.classes.files import Files
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
from general.timeutil import TSC

class MijlpaalDirectory(AAPAclass):    
    def __init__(self, mijlpaal_type: MijlpaalType, directory: str, datum: datetime.datetime, id=EMPTY_ID):
        super().__init__(id)
        self.mijlpaal_type = mijlpaal_type
        self.datum  = datum
        self.directory = directory
        self._files = Files(owner=self)
    @property
    def files(self)->Files: return self._files
    @property
    def files_list(self)->list[Files]: return self._files.as_list('files')
    def __str__(self):        
        s = f'{summary_string(self.directory, maxlen=80)} [{self.mijlpaal_type}] {TSC.timestamp_to_str(self.datum)}'
        file_str = "\n\t\t".join([file.summary(name_only=True) for file in self.files_list])
        if file_str:
            s = s + "\n\t\t"+ file_str
        return s

