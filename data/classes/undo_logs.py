from __future__ import annotations
import datetime
from enum import IntEnum
import os
from typing import Type
from data.classes.aanvragen import Aanvraag
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.classes.files import File
from main.log import log_debug, log_warning
from general.singular_or_plural import sop
from general.timeutil import TSC
from database.classes.dbConst import EMPTY_ID
from general.fileutil import summary_string
from main.options import AAPAProcessingOptions

UndoLogData=Type[Aanvraag|File]       
class UndoLogAggregator(Aggregator):
    def __init__(self, owner: UndoLog):
        super().__init__(owner=owner)
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(Verslag, 'verslagen')
        self.add_class(File, 'files')

class UndoLog(AAPAclass):
    class Action(IntEnum):
        NOLOG   = 0
        INPUT   = 1
        FORM    = 2
        MAIL    = 3
        UNDO    = 4
        DETECT  = 5
        def __str__(self):
            return self.name
    def __init__(self, action: Action, processing_mode: AAPAProcessingOptions.PROCESSINGMODE, description='',  id=EMPTY_ID, date=None, user: str=os.getlogin(), can_undo=True):
        super().__init__(id)
        self.action = action        
        self.processing_mode=processing_mode
        self.description = description
        self.date:datetime.datetime = date
        self.user = user
        self._data = UndoLogAggregator(self)
        self.can_undo = can_undo     
    @property
    def data(self)->Aggregator:
        return self._data
    @property
    def aanvragen(self)->list[Aanvraag]:
        return self._data.as_list('aanvragen', sort_key=lambda a: a.id)
    @aanvragen.setter
    def aanvragen(self, value: list[Aanvraag]):
        self._data.clear('aanvragen')
        if value:
            self._data.add(value)
    @property
    def verslagen(self)->list[Verslag]:
        return self._data.as_list('verslagen', sort_key=lambda a: a.id)
    @aanvragen.setter
    def aanvragen(self, value: list[Verslag]):
        self._data.clear('verslagen')
        if value:
            self._data.add(value)
    @property
    def files(self)->list[File]:
        return self._data.as_list('files', sort_key=lambda f: f.id)
    @files.setter
    def files(self, value: list[File]):
        self._data.clear('files')
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
    def clear_verslagen(self):
        self.verslagen = []
    def clear_files(self):
        self.files = []
    def contains(self, obj: AAPAclass)->bool:
        return self._data.contains(obj)
    @property
    def nr_aanvragen(self)->int:
        return self._data.nr_items('aanvragen')
    @property
    def nr_verslagen(self)->int:
        return self._data.nr_items('verslagen')
    @property
    def nr_files(self)->int:
        return self._data.nr_items('files')
    def is_empty(self, class_alias: str='')->bool:
        match class_alias:
            case 'aanvragen': return self.nr_aanvragen == 0
            case 'verslagen': return self.nr_verslagen == 0
            case 'files': return self.nr_files == 0
            case _: return self._data.nr_items() == 0
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
    def __str_verslagen(self)->str:
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        result = f'{self.action} {date_str} [{self.user}] ({self.id})' 
        if self.is_empty('verslagen'):
            return result + ' (geen verslagen)'
        else:
            result = result + f'!{self.nr_verslagen} {sop(self.nr_verslagen, "verslag", "verslagen")}'
            can_undo_str = 'kan worden' if self.can_undo else ''
            result = f"{result} [{can_undo_str} teruggedraaid]"
            return result + '\n\t'+ '\n\t'.join([verslag.summary() for verslag in self.verslagen])            
    def __str__(self)->str:
        return self.__str_aanvragen() if self.processing_mode == AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN else self.__str_verslagen()
    def __eq__(self, value2: UndoLog)->bool:
        if not value2:
            return False
        if self.action != value2.action or self.description != value2.description:
            return False
        if self.date != value2.date or self.user != value2.user or self.can_undo != value2.can_undo: 
            return False
        if not self._data.is_equal(value2._data):
            return False
        return True
        
    def summary(self)->str:
        log_debug(f'full action: {str(self)}')
        date_str = TSC.timestamp_to_str(self.date if self.date else datetime.datetime.now())
        if self.processing_mode == AAPAProcessingOptions.PROCESSINGMODE.AANVRAGEN:
            aanvr_str = f'{self.nr_aanvragen}' if not self.is_empty('aanvragen') else 'geen'
            return f'{date_str} (gebruiker: {self.user}): {self.description} ({aanvr_str} {sop(self.nr_aanvragen, "aanvraag", "aanvragen", False)})'
        else:
            versl_str = f'{self.nr_verslagen}' if not self.is_empty('verslagen') else 'geen'
            return f'{date_str} (gebruiker: {self.user}): {self.description} ({versl_str} {sop(self.nr_verslagen, "verslag", "verslagen", False)})'
    
