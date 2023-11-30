import datetime
import os
from pathlib import Path
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.action_logs import ActionLog
from data.classes.files import File
from data.storage.aapa_storage import AAPAStorage
from general.log import log_debug, log_error, log_info
from general.preview import Preview
from process.general.aanvraag_processor import AanvraagCreator, AanvraagProcessor
from process.general.pipeline import FilePipeline, Pipeline

class AanvragenPipeline(Pipeline):
    def __init__(self, description: str, processors: AanvraagProcessor|list[AanvraagProcessor], storage: AAPAStorage, activity: ActionLog.Action, 
                 can_undo=True, aanvragen: list[Aanvraag] = None):
        super().__init__(description, processors, storage, activity=activity, can_undo=can_undo)
        self.aanvragen = aanvragen if aanvragen else self.__read_aanvragen_from_storage()
        self.__sort_aanvragen()     
    def __read_aanvragen_from_storage(self)->list[Aanvraag]:
        log_info('Start reading aanvragen from database')
        entry_states = self.processors[0].entry_states
        result = self.storage.call_helper('aanvragen', 'read_all', states=entry_states)
        log_info('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: Aanvraag):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        if self.aanvragen:
            self.aanvragen.sort(key=comparekey, reverse=False) # TRUE ?!
    def filtered_aanvragen(self, filter_func=None)->list[Aanvraag]:
        if self.aanvragen and filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return self.aanvragen
    @property
    def processors(self)->list[AanvraagProcessor]:
        return self._processors
    def _process_aanvraag_processor(self, processor: AanvraagProcessor, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        try:
            result = processor.must_process(aanvraag, preview=preview, **kwargs) and processor.process(aanvraag, preview, **kwargs)                                                
            log_debug(f'_process_aanvraag_processor: {result}')
            return result
        except Exception as E:
            log_error(f'Fout bij processing aanvraag ({self.description}) {aanvraag.summary()}:\n\t{E}')
        log_debug(f'_process_aanvraag_processor: FALSE')
        return False
    def _process_aanvraag(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        processed = False               
        for processor in self.processors:
            log_debug(f'processor: {processor.description} {kwargs}  {processor.must_process(aanvraag, **kwargs)}')
            if not processor.in_entry_states(aanvraag.status):
                break
            if self._process_aanvraag_processor(processor, aanvraag, preview, **kwargs):
                processed = True
                log_debug(f'processed. Exit state: {processor.exit_state}')
                if processor.exit_state:
                    aanvraag.status = processor.exit_state                       
                self.storage.update(aanvraag)
                self.storage.commit()
            else:
                log_debug(f'Not processed: {processor.description} {self.action_log}')
        return processed
    def process(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        self.start_logging()
        with Preview(preview, self.storage, 'process (pipeline)'):
            if (aanvragen := self.filtered_aanvragen(filter_func)):
                for aanvraag in aanvragen:
                    if self._process_aanvraag(aanvraag, preview, **kwargs):
                        n_processed += 1            
                        self.log_aanvraag(aanvraag) 
            self.stop_logging()
        return n_processed

class AanvraagCreatorPipeline(FilePipeline):
    def __init__(self, description: str, processor: AanvraagCreator, storage: AAPAStorage, activity: ActionLog.Action, invalid_filetype: File.Type):
        super().__init__(description, processor, storage, activity=activity, invalid_filetype=invalid_filetype)
    def _skip(self, filename: str)->bool:
        return False
    def _store_new(self, aanvraag: Aanvraag):
        self.storage.create(aanvraag)
        self.log_aanvraag(aanvraag)   
    def _sorted(self, files: Iterable[Path]) -> Iterable[Path]:
        return sorted(files, key=os.path.getmtime)
