from __future__ import annotations
import datetime
import os
from pathlib import Path
import re
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.action_log import ActionLog
from data.storage import AAPAStorage
from general.fileutil import summary_string
from general.log import log_debug, log_error, log_info, log_print
from general.preview import Preview
from process.general.aanvraag_processor import AanvraagCreator, AanvraagProcessor, AanvraagProcessorBase

class PipelineException(Exception): pass

class PipelineBase:
    def __init__(self, description: str, processors: AanvraagProcessorBase|list[AanvraagProcessorBase], 
                 storage: AAPAStorage, activity: ActionLog.Action, can_undo = True):
        self._processors:list[AanvraagProcessorBase] = []
        if isinstance(processors, list):
            if not len(processors):
                raise PipelineException('Empty pipeline (no processors)')
            for processor in processors: self._processors.append(processor)
        else:
            self._processors.append(processors)
        self.storage = storage
        self.action_log = ActionLog(activity, description, can_undo=can_undo)
        self.known_files = self.storage.files.find_all_for_filetype({filetype for filetype in File.Type}).get_files()
    @property
    def description(self)->str:
        return self.action_log.description
    def start_logging(self):
        self.action_log.start()
        log_debug(f'STARTING aanvragenprocessor {self.action_log}')
    def log_aanvraag(self, aanvraag: Aanvraag):
        if aanvraag and aanvraag.status != Aanvraag.Status.DELETED:
            self.action_log.add_aanvraag(aanvraag)
    def stop_logging(self):
        self.action_log.stop()
        log_debug(f'STOPPING aanvragenprocessor {self.action_log}')
        if not self.action_log.is_empty():
            self.storage.action_logs.create(self.action_log)
        self.storage.commit()
    def is_known_file(self, filename: str)->bool: 
        return filename in {file.filename for file in self.known_files} or self.storage.files.is_known_invalid(str(filename))

class ProcessingPipeline(PipelineBase):
    def __init__(self, description: str, processors: AanvraagProcessor|list[AanvraagProcessor], storage: AAPAStorage, activity: ActionLog.Action, can_undo=True, aanvragen: list[Aanvraag] = None):
        super().__init__(description, processors, storage, activity=activity, can_undo=can_undo)
        self.aanvragen = aanvragen if aanvragen else self.__read_from_storage()
        self.__sort_aanvragen() 
    def __read_from_storage(self):
        log_info('Start reading aanvragen from database')
        entry_states = self._processors[0].entry_states
        result = self.storage.aanvragen.read_all(states=entry_states)
        log_info('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: Aanvraag):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        if self.aanvragen:
            self.aanvragen.sort(key=comparekey, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[Aanvraag]:
        if self.aanvragen and filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return self.aanvragen
    def _process_aanvraag(self, processor: AanvraagProcessor, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        try:
            result = processor.must_process(aanvraag, **kwargs) and processor.process(aanvraag, preview, **kwargs)                                                
            log_debug(f'_process_aanvraag: {result}')
            return result
        except Exception as E:
            log_error(f'Fout bij processing aanvraag ({self.description}) {aanvraag.summary()}:\n\t{E}')
        log_debug(f'_process_aanvraag: FALSE')
        return False
    def process(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        self.start_logging()
        with Preview(preview, self.storage, 'process (pipeline)'):
            if (aanvragen := self.filtered_aanvragen(filter_func)):
                for aanvraag in aanvragen:
                    processed = 0                
                    for processor in self._processors:
                        log_debug(f'processor: {processor.description} {kwargs}  {processor.must_process(aanvraag, **kwargs)}')
                        if not processor.in_entry_states(aanvraag.status):
                            break
                        if self._process_aanvraag(processor, aanvraag, preview, **kwargs):
                            processed += 1
                            log_debug(f'processed. Exit state: {processor.exit_state}')
                            if processor.exit_state:
                                aanvraag.status = processor.exit_state                       
                            self.storage.aanvragen.update(aanvraag)
                            self.storage.commit()
                        else:
                            log_debug(f'Not processed: {processor.description} {self.action_log}')
                    if processed > 0:
                        n_processed += 1            
                        self.log_aanvraag(aanvraag) 
            self.stop_logging()
        return n_processed

class CreatingPipeline(PipelineBase):
    def __init__(self, description: str, processors: AanvraagProcessorBase|list[AanvraagProcessorBase], storage: AAPAStorage, skip_directories: set[Path]={}, skip_files: list[str]=[]):
        super().__init__(description, processors, storage, activity=ActionLog.Action.SCAN)  
        self.skip_directories:list[Path] = skip_directories
        self.skip_files:list[re.Pattern] = [re.compile(rf'{pattern}\.pdf', re.IGNORECASE) for pattern in skip_files]        
    def _in_skip_directory(self, filename: Path)->bool:
        for skip in self.skip_directories:
            if filename.is_relative_to(skip):
                return True
        return False
    def _skip_file(self, filename: Path)->bool:
        for pattern in self.skip_files:
            if pattern.match(str(filename)):
                return True 
        return False
    def _process_file(self, processor: AanvraagCreator, filename: str, preview=False, **kwargs)->bool:
        if processor.must_process_file(filename, self.storage, **kwargs):
            try:
                aanvraag = processor.process_file(filename, self.storage, preview, **kwargs)
                if aanvraag is None:
                    return False
                self.storage.aanvragen.create(aanvraag)
                self.storage.commit()
                self.log_aanvraag(aanvraag)
                return True
            except Exception as E:
                log_error(f'Fout bij processing file ({self.description}) {summary_string(filename, maxlen=96)}:\n\t{E}')
        return False    
    def process(self, files: Iterable[Path], preview=False, **kwargs)->int:
        n_processed = 0
        with Preview(preview, self.storage, 'process (creator)'):
            self.start_logging()
            for filename in sorted(files, key=os.path.getmtime):
                if self._in_skip_directory(filename):
                    continue                    
                if self._skip_file(filename) and not self.is_known_file(filename):
                    log_print(f'Overslaan: {summary_string(filename, maxlen=100)}')
                    self.storage.files.store_invalid(str(filename))
                    continue
                file_processed = True
                for processor in self._processors:
                    log_debug(f'processor: {processor.__class__} {filename} {kwargs}  {processor.must_process_file(str(filename), self.storage, **kwargs)}')
                    if not self._process_file(processor, str(filename), preview, **kwargs):
                        file_processed = False
                        break                
                if file_processed:
                    n_processed += 1
            self.stop_logging()     
            log_debug('end process (creator)')       
        return n_processed
