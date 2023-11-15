from __future__ import annotations
import datetime
from enum import IntEnum
import os
from typing import Type
from data.classes.aanvragen import Aanvraag
from data.classes.aggregator import Aggregator
from data.classes.files import File
from debug.debug import classname
from general.log import log_debug, log_warning
from general.singular_or_plural import sop
from general.timeutil import TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string

ActionLogData=Type[Aanvraag|File]       
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
        self.data = self.__init_data()
        self.can_undo = can_undo
    def __init_data(self)->Aggregator:
        result = Aggregator()
        result.add_class(Aanvraag, 'aanvraag')
        result.add_class(File, 'invalid_file')
    @property
    def aanvragen(self)->list[Aanvraag]:
        return self.data.as_list('aanvraag')
    @aanvragen.setter
    def aanvragen(self, value: list[Aanvraag]):
        self.data.clear('aanvraag')
        self.data.add(value)
    @property
    def invalid_files(self)->list[File]:
        return self.data.as_list('invalid_file')
    @invalid_files.setter
    def invalid_files(self, value: list[File]):
        self.data.clear('invalid_file')
        self.data.add(value)
    def start(self):
        self.clear_aanvragen()
        self.clear_invalid_files()
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add(self, object: ActionLogData, duplicate_warning=False):
        if duplicate_warning and self.data.contains(object):
            log_warning(f'Duplicate key in ActionLog: {str(object)} is already registered')
        self.data.add(object)
    def remove(self, object: ActionLogData)->ActionLogData:
        self.data.remove(object)
    def clear_aanvragen(self):
        self.aanvragen = []
    def clear_invalid_files(self):
        self.invalid_files = []
    @property
    def nr_aanvragen(self)->int:
        return len(self.aanvragen)
    @property
    def nr_invalid_files(self)->int:
        return len(self.aanvragen)
    def is_empty(self, class_alias: str='')->bool:
        match class_alias:
            case 'aanvraag': return self.nr_aanvragen == 0
            case 'invalid_file': return self.nr_invalid_files == 0
            case _: return self.nr_aanvragen == 0 and self.nr_invalid_files == 0
    def __str_aanvragen(self)->str:
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        result = f'{self.action} {date_str} [{self.user}] ({self.id})' 
        if self.is_empty('aanvraag'):
            return result + ' (geen aanvragen)'
        else:
            result = result + f'!{self.nr_aanvragen} {sop(self.nr_aanvragen, "aanvraag", "aanvragen")}'
            can_undo_str = 'kan worden' if self.can_undo else ''
            result = f"{result} [{can_undo_str} teruggedraaid]"
            return result + '\n\t'+ '\n\t'.join([summary_string(aanvraag) for aanvraag in self.aanvragen])            
    def __str__(self)->str:
        return self.__str_aanvragen()
    def summary(self)->str:
        log_debug(f'full action: {str(self)}')
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        aanvr_str = f'{self.nr_aanvragen}' if not self.is_empty('aanvraag') else 'geen'
        return f'{date_str} (gebruiker: {self.user}): {self.description} ({aanvr_str} {sop(self.nr_aanvragen, "aanvraag", "aanvragen", False)})'
