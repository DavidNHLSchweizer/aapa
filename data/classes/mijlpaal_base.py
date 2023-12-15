from __future__ import annotations
import datetime
from data.classes.aapa_class import AAPAclass
from data.classes.bedrijven import Bedrijf
from data.classes.const import MijlpaalType, MijlpaalBeoordeling
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class MijlpaalBase(AAPAclass):            
    Beoordeling = MijlpaalBeoordeling
    def __init__(self, mijlpaal_type: MijlpaalType, student:Student, datum: datetime.datetime, bedrijf: Bedrijf = None, kans=0, status=0, 
                 beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        super().__init__(id)
        self.mijlpaal_type = mijlpaal_type
        self.datum = datum
        self.student = student
        self.bedrijf = bedrijf
        self.titel = titel
        self._files = Files(owner=self)
        self.kans = kans
        self.status = status
        self.beoordeling = beoordeling
    def relevant_attributes(self)->list[str]:
        return {'datum', 'student', 'bedrijf', 'mijlpaal_type'}
    @property
    def files(self)->Files: return self._files
    @property
    def files_list(self)->list[Files]: return self._files.as_list('files')
    def register_file(self, filename: str, filetype: File.Type, mijlpaal_type: MijlpaalType):
        self.files.add(File(filename=filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, mijlpaal_type=mijlpaal_type))
    def unregister_file(self, filetype: File.Type):
        self.files.remove_filetype(filetype)
    def summary(self)->str:
        return str(self)
    def default_filetype(self)->File.Type:
        match self.mijlpaal_type:
            case MijlpaalType.PVA: return File.Type.PVA
            case MijlpaalType.ONDERZOEKS_VERSLAG: return File.Type.ONDERZOEKS_VERSLAG
            case MijlpaalType.TECHNISCH_VERSLAG: return File.Type.TECHNISCH_VERSLAG
            case MijlpaalType.EIND_VERSLAG: return File.Type.EIND_VERSLAG
            case _: return File.Type.UNKNOWN
    def __str__(self):        
        s = f'{TSC.get_date_str(self.datum)}: {self.mijlpaal_type} ({self.kans}) {str(self.student)} ' +\
              f'"{self.titel}" [{str(self.status)}]'
        s = s + "\n\tDirectory:" + str(self.directory)
        if self.beoordeling != MijlpaalBeoordeling.TE_BEOORDELEN:
            s = s + f' ({str(self.beoordeling)})'
        return s