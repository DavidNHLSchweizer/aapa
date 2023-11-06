from __future__ import annotations
import datetime
from enum import IntEnum
import os
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from general.log import log_debug
from general.singular_or_plural import sop
from general.timeutil import TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
       
class ActionLog:
    class Action(IntEnum):
        NOLOG   = 0
        SCAN    = 1
        FORM    = 2
        MAIL    = 3
        UNDO    = 4
        DETECT  = 5    
        def __str__(self):
            return self.name
    def __init__(self, action: Action, description='',  id=EMPTY_ID, date=None, user: str=os.getlogin(), can_undo=True):
        self.action = action        
        self.id = id #KEY
        self.description = description
        self.date:datetime.datetime = date
        self.user = user
        self.aanvragen: list[Aanvraag]=[]
        self.invalid_files: list[File]=[] 
        self.can_undo = can_undo
    def start(self):
        self.aanvragen = []
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add_aanvraag(self, aanvraag: Aanvraag):
        self.aanvragen.append(aanvraag)
    def remove_aanvraag(self, aanvraag: Aanvraag):
        try:
            self.aanvragen.remove(aanvraag)
        except ValueError as E:
            pass
    def add_invalid_file(self, file: File):
        self.invalid_files.append(file)
    def remove_invalid_file(self, file: File):
        try:
            self.invalid_files.remove(file)
        except ValueError as E:
            pass
    def clear_aanvragen(self):
        self.aanvragen = []
    def clear_invalid_files(self):
        self.invalid_files = []
    @property
    def nr_aanvragen(self)->int:
        return len(self.aanvragen)
    def is_empty(self)->bool:
        return self.nr_aanvragen == 0
    def __str__(self)->str:
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        result = f'{self.action} {date_str} [{self.user}] ({self.id})' 
        if self.is_empty():
            return result + ' (geen aanvragen)'
        else:
            result = result + f'!{self.nr_aanvragen} {sop(self.nr_aanvragen, "aanvraag", "aanvragen")}'
            can_undo_str = 'kan worden' if self.can_undo else ''
            result = f"{result} [{can_undo_str} teruggedraaid]"
            return result + '\n\t'+ '\n\t'.join([summary_string(aanvraag) for aanvraag in self.aanvragen])
    def summary(self)->str:
        log_debug(f'full action: {str(self)}')
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        aanvr_str = f'{self.nr_aanvragen}' if not self.is_empty() else 'geen'
        return f'{date_str} (gebruiker: {self.user}): {self.description} ({aanvr_str} {sop(self.nr_aanvragen, "aanvraag", "aanvragen", False)})'
