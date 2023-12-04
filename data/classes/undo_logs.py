from __future__ import annotations
import datetime
from enum import IntEnum
import os
from typing import Type
from data.classes.aanvragen import Aanvraag
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.files import File
from general.log import log_debug, log_warning
from general.singular_or_plural import sop
from general.timeutil import TSC
from database.dbConst import EMPTY_ID
from general.fileutil import summary_string

UndoLogData=Type[Aanvraag|File]       
class UndoLogAggregator(Aggregator):
    def __init__(self, owner: UndoLog):
        super().__init__(owner=owner)
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(File, 'invalid_files')

class UndoLog(AAPAclass):
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
        super().__init__(id)
        self.action = action        
        self.description = description
        self.date:datetime.datetime = date
        self.user = user
        self._data = UndoLogAggregator(self)
        self.can_undo = can_undo     
    @property
    def aanvragen(self)->list[Aanvraag]:
        return self._data.as_list('aanvragen', sort_key=lambda a: a.id)
    @aanvragen.setter
    def aanvragen(self, value: list[Aanvraag]):
        self._data.clear('aanvragen')
        if value:
            self._data.add(value)
    @property
    def invalid_files(self)->list[File]:
        return self._data.as_list('invalid_files', sort_key=lambda f: f.id)
    @invalid_files.setter
    def invalid_files(self, value: list[File]):
        self._data.clear('invalid_files')
        if value:
            self._data.add(value)
    def start(self):
        self._data.clear()
        self.date = datetime.datetime.now()
    def stop(self):
        pass # voor latere toevoegingen
    def add(self, object: UndoLogData, duplicate_warning=False):
        if duplicate_warning and self._data.contains(object):
            log_warning(f'Duplicate key in UndoLog: {str(object)} is already registered')
        self._data.add(object)
    def remove(self, object: UndoLogData)->UndoLogData:
        self._data.remove(object)
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
            case 'aanvragen': return self.nr_aanvragen == 0
            case 'invalid_files': return self.nr_invalid_files == 0
            case _: return self.nr_aanvragen == 0 and self.nr_invalid_files == 0
    def __str_aanvragen(self)->str:
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        result = f'{self.action} {date_str} [{self.user}] ({self.id})' 
        if self.is_empty('aanvragen'):
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
        aanvr_str = f'{self.nr_aanvragen}' if not self.is_empty('aanvragen') else 'geen'
        return f'{date_str} (gebruiker: {self.user}): {self.description} ({aanvr_str} {sop(self.nr_aanvragen, "aanvraag", "aanvragen", False)})'
