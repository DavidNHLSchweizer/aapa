from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.base_dirs import BaseDir
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.log import log_print
from general.timeutil import TSC

class StudentMilestone:            
    class Beoordeling(IntEnum):
        TE_BEOORDELEN = 0
        ONVOLDOENDE   = 1
        VOLDOENDE     = 2
        def __str__(self):
            _MB_STRS = {StudentMilestone.Beoordeling.TE_BEOORDELEN: '', StudentMilestone.Beoordeling.ONVOLDOENDE: 'onvoldoende', StudentMilestone.Beoordeling.VOLDOENDE: 'voldoende'}
            return _MB_STRS[self]
    class Type(IntEnum):
        UNKNOWN             = 0
        AANVRAAG            = 1
        PVA                 = 2
        ONDERZOEKS_VERSLAG  = 3
        TECHNISCH_VERSLAG   = 4
        EIND_VERSLAG        = 5
        def __str__(self):
            _MT_STRS = {StuMiType.UNKNOWN: '', StuMiType.AANVRAAG: 'aanvraag', StuMiType.PVA: 'plan van aanpak', 
                        StuMiType.ONDERZOEKS_VERSLAG: 'onderzoeksverslag', StuMiType.TECHNISCH_VERSLAG: 'technisch verslag',
                        StuMiType.EIND_VERSLAG: 'eindverslag'                       
            }
            return _MT_STRS[self]
    def __init__(self, milestone_type: StuMiType, student:Student, datum: datetime.datetime, kans=1, status=0, beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        self.milestone_type = milestone_type
        self._id = id
        self.datum = datum
        self.student = student
        self.titel = titel
        self._files = Files(id)
        self.kans = kans
        self.status = status
        self.beoordeling = beoordeling
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        self._id = value
        self._files.aanvraag_id = value
    @property
    def files(self)->Files:
        return self._files
    @files.setter
    def files(self, files: Files):
        for ft in File.Type:
            if ft != File.Type.UNKNOWN:
                self.files.set_file(files.get_file(ft))
    def register_file(self, filename: str, filetype: File.Type):
        self.files.set_file(File(filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, aanvraag_id=self.id))
    def unregister_file(self, filetype: File.Type):
        self.files.reset_file(filetype)
    def summary(self)->str:
        return str(self)
StuMiType = StudentMilestone.Type

class StudentMilestones:
    def __init__(self, student: Student, base_dir: BaseDir = None, id: int = EMPTY_ID):
        self.id = id #key
        self.student = student
        self.base_dir = base_dir
        self._milestones: list[StudentMilestone] = []
    @property
    def milestones(self)->list[StudentMilestone]:
        return self._milestones
    def get(self, milestone_type: set[StuMiType])->list[StudentMilestone]:
        return [milestone for milestone in self._milestones if milestone.milestone_type in milestone_type]  
    def add(self, milestone: StudentMilestone):
        self.milestones.append(milestone)
        self._standardize()
    def _standardize(self):
        self.milestones.sort(key=lambda ms: (ms.milestone_type, ms.datum))
        cur_type = StuMiType.UNKNOWN
        for milestone in self.milestones:
            if milestone.milestone_type != cur_type:
                kans = 1
                cur_type = milestone.milestone_type
            else:
                kans += 1
            milestone.kans = kans

    # def get_milestone(self, milestone_type: StuMiType)->StudentMilestone:
    #     return self._milestones.get(milestone_type, None)
    # def set_milestone(self, milestone: StudentMilestone):        
    #     if milestone:
    #         self._milestones[milestone.milestone_type] = milestone
    # def reset_milestone(self, milestone_type: StuMiType):
    #     self._milestones[milestone_type] = None
