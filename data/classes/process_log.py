from __future__ import annotations
import datetime
from enum import IntEnum
import os
from data.classes.aanvragen import Aanvraag
from general.timeutil import TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string
       
class ProcessLog:
    class Action(IntEnum):
        NOLOG   = 0
        CREATE  = 1
        SCAN    = 2
        MAIL    = 3
        REVERT  = 4      
    def __init__(self, action: Action, description='',  id=EMPTY_ID, date=None, user: str=os.getlogin(), rolled_back=False):
        self.action = action        
        self.id = id #KEY
        self.description = description
        self.date = date
        self.user = user
        self.aanvragen: list[Aanvraag]=[]
        self.rolled_back = rolled_back
    def start(self):
        self.aanvragen = []
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add_aanvraag(self, aanvraag: Aanvraag):
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
