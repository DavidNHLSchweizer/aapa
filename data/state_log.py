from __future__ import annotations
import datetime
from enum import Enum
import os
from data.classes import AanvraagInfo, AanvraagStatus, FileType, AanvraagBeoordeling
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
        SCAN = 1
        MAIL = 2
    def __init__(self, activity: Activity):
        self.date: datetime = datetime.datetime.now()
        self.user: str = os.getlogin()
        self.activity = activity        
        self.aanvragen: list[AanvraagInfo] = []
    def add_aanvraag(self, aanvraag: AanvraagInfo):
        self.aanvragen.append(aanvraag)

