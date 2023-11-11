from __future__ import annotations
import datetime
from enum import IntEnum
from data.classes.base_dirs import BaseDir
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.log import log_print
from general.timeutil import TSC

class Milestone:            
    class Beoordeling(IntEnum):
        TE_BEOORDELEN = 0
        ONVOLDOENDE   = 1
        VOLDOENDE     = 2
        def __str__(self):
            _MB_STRS = {Milestone.Beoordeling.TE_BEOORDELEN: '', Milestone.Beoordeling.ONVOLDOENDE: 'onvoldoende', Milestone.Beoordeling.VOLDOENDE: 'voldoende'}
            return _MB_STRS[self]
    class Type(IntEnum):
        UNKNOWN             = 0
        AANVRAAG            = 1
        PVA                 = 2
        ONDERZOEKS_VERSLAG  = 3
        TECHNISCH_VERSLAG   = 4
        EIND_VERSLAG        = 5
        def __str__(self):
            _MT_STRS = {Milestone.Type.UNKNOWN: '', Milestone.Type.AANVRAAG: 'aanvraag', Milestone.Type.PVA: 'plan van aanpak', 
                        Milestone.Type.ONDERZOEKS_VERSLAG: 'onderzoeksverslag', Milestone.Type.TECHNISCH_VERSLAG: 'technisch verslag',
                        Milestone.Type.EIND_VERSLAG: 'eindverslag'                       
            }
            return _MT_STRS[self]
    def __init__(self, milestone_type: Milestone.Type, student:Student, datum: datetime.datetime, bedrijf: Bedrijf = None, kans=1, status=0, beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        self.milestone_type = milestone_type
        self._id = id
        self.datum = datum
        self.student = student
        self.bedrijf = bedrijf
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

class StudentMilestones:
    def __init__(self, student: Student, base_dir: BaseDir = None, id: int = EMPTY_ID):
        self.id = id #key
        self.student = student
        self.base_dir = base_dir
        self._milestones: list[Milestone] = []
    @property
    def milestones(self)->list[Milestone]:
        return self._milestones
    def get(self, milestone_type: set[Milestone.Type])->list[Milestone]:
        return [milestone for milestone in self._milestones if milestone.milestone_type in milestone_type]  
    def add(self, milestone: Milestone):
        self.milestones.append(milestone)
        self._standardize()
    def _standardize(self):
        self.milestones.sort(key=lambda ms: (ms.milestone_type, ms.datum))
        cur_type = Milestone.Type.UNKNOWN
        for milestone in self.milestones:
            if milestone.milestone_type != cur_type:
                kans = 1
                cur_type = milestone.milestone_type
            else:
                kans += 1
            milestone.kans = kans

    