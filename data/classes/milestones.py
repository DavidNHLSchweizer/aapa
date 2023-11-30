from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.aapa_class import AAPAclass
from data.classes.base_dirs import BaseDir
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Milestone(AAPAclass):            
    class Beoordeling(IntEnum):
        TE_BEOORDELEN = 0
        ONVOLDOENDE   = 1
        VOLDOENDE     = 2
        def __str__(self):
            _MB_STRS = {Milestone.Beoordeling.TE_BEOORDELEN: '', Milestone.Beoordeling.ONVOLDOENDE: 'onvoldoende', Milestone.Beoordeling.VOLDOENDE: 'voldoende'}
            return _MB_STRS[self]
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

class StudentMilestones(AAPAclass):
    def __init__(self, student: Student, base_dir: BaseDir = None, id: int = EMPTY_ID):
        super().__init__(id)        
        self.student = student
        self.base_dir = base_dir
        self._milestones: list[Milestone] = []
    @property
    def milestones(self)->list[Milestone]: return self._milestones
    # def get(self, milestone_type: set[Verslag.Type])->list[Milestone]:
    #     return [milestone for milestone in self._milestones if milestone.milestone_type in milestone_type]  
    def add(self, milestone: Milestone):
        self.milestones.append(milestone)
        self._standardize()
    def _standardize(self):
        pass
        # self.milestones.sort(key=lambda ms: (ms.milestone_type, ms.datum))
        # cur_type = Verslag.Type.UNKNOWN
        # for milestone in self.milestones:
        #     if milestone.milestone_type != cur_type:
        #         kans = 1
        #         cur_type = milestone.milestone_type
        #     else:
        #         kans += 1
        #     milestone.kans = kans

    