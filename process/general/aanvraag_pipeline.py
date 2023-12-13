import datetime
import os
from pathlib import Path
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.undo_logs import UndoLog
from data.classes.files import File
from data.storage.aapa_storage import AAPAStorage
from debug.debug import ITEM_DEBUG_DIVIDER, MINOR_DEBUG_DIVIDER
from general.log import log_debug, log_error, log_info
from general.preview import Preview
from process.general.aanvraag_processor import AanvraagCreator, AanvraagProcessor
from process.general.pipeline import FilePipeline, Pipeline

class AanvragenPipeline(Pipeline):
    def __init__(self, description: str, processors: AanvraagProcessor|list[AanvraagProcessor], storage: AAPAStorage, activity: UndoLog.Action, 
                 can_undo=True, aanvragen: list[Aanvraag] = None):
        super().__init__(description, processors, storage, activity=activity, can_undo=can_undo)
        self.aanvragen = aanvragen if aanvragen else self.__read_aanvragen_from_storage()
        self.__sort_aanvragen()     
    def __read_aanvragen_from_storage(self)->list[Aanvraag]:
        entry_states = self.processors[0].entry_states
        log_info(f'Start reading aanvragen from database. Entry_states: {entry_states}')
        result = self.storage.find_all('aanvragen', 
                                       where_attributes='status', 
                                       where_values=entry_states)
                                    #    where_values={Aanvraag.Status.valid_states()})
        log_info(f'End reading aanvragen from database. {len} aanvragen read.')
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
            log_debug(ITEM_DEBUG_DIVIDER)
            log_debug(f'processor: {processor.description} [args: {kwargs}]  {processor.must_process(aanvraag, **kwargs)}')
            if not processor.in_entry_states(aanvraag.status):
                break
            if self._process_aanvraag_processor(processor, aanvraag, preview, **kwargs):
                processed = True
                log_debug(f'processed. Exit state: {processor.exit_state}')
                if processor.exit_state:
                    aanvraag.status = processor.exit_state                       
                if not processor.read_only:
                    self.storage.update('aanvragen', aanvraag)
                    self.storage.commit()
            else:
                log_debug(f'Not processed: {processor.description} {self.undo_log}')
            log_debug(ITEM_DEBUG_DIVIDER)
        return processed
    def process(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        self.start_logging()
        with Preview(preview, self.storage, 'process (pipeline)'):
            log_debug(MINOR_DEBUG_DIVIDER)
            if (aanvragen := self.filtered_aanvragen(filter_func)):
                for aanvraag in aanvragen:
                    if self._process_aanvraag(aanvraag, preview, **kwargs):
                        n_processed += 1            
                        self.log_aanvraag(aanvraag) 
            self.stop_logging()
            log_debug(MINOR_DEBUG_DIVIDER)
        return n_processed

class AanvraagCreatorPipeline(FilePipeline):
    def __init__(self, description: str, processor: AanvraagCreator, storage: AAPAStorage, activity: UndoLog.Action, invalid_filetype: File.Type):
        super().__init__(description, processor, storage, activity=activity, invalid_filetype=invalid_filetype)
    def _skip(self, filename: str)->bool:
        return False
    def _store_new(self, aanvraag: Aanvraag):
        self.storage.create('aanvragen', aanvraag)
        self.log_aanvraag(aanvraag)   
    def _sorted(self, files: Iterable[Path]) -> Iterable[Path]:
        return sorted(files, key=os.path.getmtime)
