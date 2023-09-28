from __future__ import annotations
import datetime
from enum import IntEnum
import os
from data.classes.aanvragen import Aanvraag
from general.timeutil import TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
       
class ActionLog:
    class Action(IntEnum):
        NOLOG   = 0
        SCAN    = 1
        FORM    = 2
        MAIL    = 3
        UNDO  = 4      
    def __init__(self, action: Action, description='',  id=EMPTY_ID, date=None, user: str=os.getlogin(), can_undo=True):
        self.action = action        
        self.id = id #KEY
        self.description = description
        self.date = date
        self.user = user
        self.aanvragen: list[Aanvraag]=[]
        self.can_undo = can_undo
    def start(self):
        self.aanvragen = []
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add_aanvraag(self, aanvraag: Aanvraag):
        self.aanvragen.append(aanvraag)
    def delete_aanvraag(self, aanvraag: Aanvraag):
        try:
            self.aanvragen.remove(aanvraag)
        except ValueError as E:
            pass
    @property
    def nr_aanvragen(self)->int:
        return len(self.aanvragen)
    def is_empty(self)->bool:
        return self.nr_aanvragen == 0
    def __str__(self)->str:
        result = f'{self.action} {TSC.timestamp_to_str(self.date)} [{self.user}] ({self.id}) !{self.nr_aanvragen} aanvragen:'
        if self.is_empty():
            return result + ' (geen aanvragen)'
        can_undo_str = 'kan worden' if self.can_undo else ''
        result = f"{result} [{can_undo_str} teruggedraaid]"
        return result + '\n\t'+ '\n\t'.join([summary_string(aanvraag) for aanvraag in self.aanvragen])
