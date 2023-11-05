from __future__ import annotations
from enum import IntEnum
from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
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
            _MT_STRS = {StudentMilestone.Type.UNKNOWN: '', StudentMilestone.Type.AANVRAAG: 'aanvraag', StudentMilestone.Type.PVA: 'plan van aanpak', 
                        StudentMilestone.Type.ONDERZOEKS_VERSLAG: 'onderzoeksverslag', StudentMilestone.Type.TECHNISCH_VERSLAG: 'technisch verslag',
                        StudentMilestone.Type.EIND_VERSLAG: 'eindverslag'                       
            }
            return _MT_STRS[self]
    def __init__(self, milestone_type: StudentMilestone.Type, student:Student, status=0, beoordeling=Beoordeling.TE_BEOORDELEN, titel='', id=EMPTY_ID):
        self.milestone_type = milestone_type
        self._id = id
        self.student = student
        self.titel = titel
        self._files = Files(id)
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
