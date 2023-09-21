from __future__ import annotations
import datetime
from enum import IntEnum
import os
from data.classes import AanvraagInfo, AanvraagStatus, FileType, AanvraagBeoordeling, TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
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
    def create(self, activity: ProcessLog.Action):
        match activity:
            case ProcessLog.Action.SCAN:
                return ScanStateChange()
            case ProcessLog.Action.MAIL:
                return MailStateChange()
            case _:
                return None
         
class ProcessLog:
    class Action(IntEnum):
        NOLOG   = 0
        CREATE  = 1
        SCAN    = 2
        MAIL    = 3
        REVERT  = 4
        
    def __init__(self, action: Action, description='', id=EMPTY_ID, date=None, user: str=os.getlogin(), rolled_back=False):
        self.action = action        
        self.id = id #KEY
        self.description = description
        self.date = date
        self.user = user
        self.aanvragen: list[AanvraagInfo]=[]
        self.rolled_back = rolled_back
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
    def is_rolled_back(self)->bool:
        return self.rolled_back
    def __str__(self)->str:
        result = f'{self.action} {TSC.timestamp_to_str(self.date)} [{self.user}] ({self.id}):'
        if self.is_empty():
            return result + ' (geen aanvragen)'
        if self.is_rolled_back():
            result = result + ' [teruggedraaid]'
        return result + '\n\t'+ '\n\t'.join([summary_string(aanvraag) for aanvraag in self.aanvragen])
