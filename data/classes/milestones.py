from __future__ import annotations
import datetime
from data.classes.aapa_class import AAPAclass
from data.classes.bedrijven import Bedrijf
from data.classes.const import MilestoneBeoordeling
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Milestone(AAPAclass):            
    Beoordeling = MilestoneBeoordeling
    def __init__(self, student:Student, datum: datetime.datetime, bedrijf: Bedrijf = None, kans=0, status=0, beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        super().__init__(id)
        self.datum = datum
        self.student = student
        self.bedrijf = bedrijf
        self.titel = titel
        self._files = Files(owner=self)
        self.kans = kans
        self.status = status
        self.beoordeling = beoordeling
    def relevant_attributes(self)->list[str]:
        return {'datum', 'student', 'bedrijf'}
    @property
    def files(self)->Files: return self._files
    def register_file(self, filename: str, filetype: File.Type):
        self.files.add(File(filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype))
    def unregister_file(self, filetype: File.Type):
        self.files.remove_filetype(filetype)
    def summary(self)->str:
        return str(self)

