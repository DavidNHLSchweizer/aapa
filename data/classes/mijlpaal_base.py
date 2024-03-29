from __future__ import annotations
import datetime
from pathlib import Path
from data.general.aapa_class import AAPAclass
from data.classes.bedrijven import Bedrijf
from data.general.const import MijlpaalType, MijlpaalBeoordeling
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.classes.dbConst import EMPTY_ID
from general.timeutil import TSC

class MijlpaalBase(AAPAclass):            
    def __init__(self, mijlpaal_type: MijlpaalType, datum: datetime.datetime, kans=0, id=EMPTY_ID):
        super().__init__(id)
        self.mijlpaal_type = mijlpaal_type
        self.datum = datum
        self.kans = kans
    def relevant_attributes(self)->set[str]:
        return {'datum', 'mijlpaal_type'}
        # return {'datum', 'mijlpaal_type', 'kans'} 
    def __eq__(self, value2: MijlpaalBase)->bool:
        if not value2:
            return False
        if self.mijlpaal_type != value2.mijlpaal_type:
            return False
        if self.datum != value2.datum:
            return False
        if self.kans != value2.kans:
            return False
        return True

class MijlpaalGradeable(MijlpaalBase):            
    Beoordeling = MijlpaalBeoordeling
    def __init__(self, mijlpaal_type: MijlpaalType, student:Student, datum: datetime.datetime, bedrijf: Bedrijf = None, kans=0, status=0, 
                 beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        super().__init__(mijlpaal_type=mijlpaal_type, datum=datum, kans=kans, id=id)
        self.student = student
        self.bedrijf = bedrijf
        self.titel = titel
        self.status = status
        self.beoordeling = beoordeling
        self._files = Files(owner=self)
    @property
    def files(self)->Files: return self._files
    def get_directory(self)->str:
        if files := self.files_list:
            return Path(files[0].filename).parent
        return None            
    def get_base_file(self)->str:
        if files := self.files_list:
            for file in files:
                if file.filetype == self.mijlpaal_type.default_filetype():
                    return file.filename
        return None            
    @property
    def files_list(self)->list[File]: return self._files.as_list('files')
    def register_file(self, filename: str, filetype: File.Type, mijlpaal_type: MijlpaalType)->File:
        result = File(filename=filename, timestamp=TSC.AUTOTIMESTAMP, digest=File.AUTODIGEST, filetype=filetype, mijlpaal_type=mijlpaal_type)
        if self.files.contains(result):
            return self.files.find_filename(filename)
        else:
            self.files.add(result)
        return result    
    def unregister_file(self, filetype: File.Type):
        self.files.remove_filetype(filetype)
    def ensure_files_timestamp_and_digest(self):
        for file in self.files_list:
            file.ensure_timestamp_and_digest()
    def get_directory(self, filetype: File.Type)->str:
        for file in self.files_list:
            if file.filetype == filetype:
                return str(Path(file.filename).parent)
        return None
    def relevant_attributes(self) -> set[str]:
        return super().relevant_attributes() | {'student', 'bedrijf'}
    def summary(self)->str:
        return str(self)
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        s = s + "\n\tDirectory:" + str(self.directory)
        if self.beoordeling != MijlpaalBeoordeling.TE_BEOORDELEN:
            s = s + f' ({str(self.beoordeling)})'
        return s
    def __eq__(self, value2: MijlpaalGradeable)->bool:
        if not super().__eq__(value2):
            return False
        if self.student != value2.student:
            return False 
        if self.bedrijf!=value2.bedrijf:
            return False
        if self.titel != value2.titel:
            return False
        if self.status != value2.status:
            return False
        if self.beoordeling != value2.beoordeling:
            return False
        if not self.files.is_equal(value2.files):
            return False
        return True
