from __future__ import annotations
import datetime
from enum import Enum
import os
from data.classes import AanvraagInfo, AanvraagStatus, FileType, AanvraagBeoordeling
from database.dbConst import EMPTY_ID
from general.singleton import Singleton

class StateChangeSummary:
    def __init__(self, initial_state: AanvraagStatus, final_states: set[AanvraagStatus], created_file_types: list[FileType], initial_beoordeling = AanvraagBeoordeling.TE_BEOORDELEN):
        self.initial_state = initial_state
        self.initial_beoordeling = initial_beoordeling
        self._final_states = final_states
        self._created_file_types = created_file_types
     
class ScanStateChange(StateChangeSummary):
    def __init__(self):
        super().__init__(AanvraagStatus.INITIAL, {AanvraagStatus.INITIAL, AanvraagStatus.NEEDS_GRADING},
                         [FileType.TO_BE_GRADED_DOCX, FileType.COPIED_PDF, FileType.DIFFERENCE_HTML])

class MailStateChange(StateChangeSummary):
    def __init__(self):
        super().__init__(AanvraagStatus.NEEDS_GRADING, {AanvraagStatus.NEEDS_GRADING, AanvraagStatus.GRADED, 
                                                        AanvraagStatus.ARCHIVED, AanvraagStatus.MAIL_READY},
                         [FileType.GRADED_PDF])
        
class StateChangeFactory(Singleton):
    def create(self, activity: ProcessLog.Activity):
        match activity:
            case ProcessLog.Activity.SCAN:
                return ScanStateChange()
            case ProcessLog.Activity.MAIL:
                return MailStateChange()
            case _:
                return None
            
class ProcessLog:
    class Activity(Enum):
        NOLOG   = 0
        CREATE  = 1
        SCAN    = 2
        MAIL    = 3
        REVERT  = 4
        
    def __init__(self, activity: Activity, description='', id=EMPTY_ID, date=None, user: str=os.getlogin()):
        self.activity = activity        
        self.id = id #KEY
        self.description = description
        self.date = date
        self.user = user
        self.aanvragen: list[AanvraagInfo]=None
    def start(self):
        self.aanvragen = []
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add_aanvraag(self, aanvraag: AanvraagInfo):
        self.aanvragen.append(aanvraag)
    @property
    def nr_aanvragen(self)->int:
        return len(self.aanvragen)
    def is_empty(self)->bool:
        return self.nr_aanvragen == 0
