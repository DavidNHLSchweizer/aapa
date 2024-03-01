import datetime
from data.classes.undo_logs import UndoLog
from data.classes.verslagen import Verslag
from debug.debug import ITEM_DEBUG_DIVIDER, MINOR_DEBUG_DIVIDER
from main.log import log_debug, log_error, log_info
from main.options import AAPAProcessingOptions
from process.general.preview import Preview
from storage.aapa_storage import AAPAStorage
from process.general.pipeline import FilePipeline, Pipeline
from process.general.verslag_processor import VerslagImporter, VerslagProcessor
from storage.queries.verslagen import VerslagenQueries
from main.config import config


class VerslagenPipeline(Pipeline):
    def __init__(self, description: str, processors: VerslagProcessor|list[VerslagProcessor], storage: AAPAStorage, activity: UndoLog.Action, 
                 can_undo=True, verslagen: list[Verslag] = None):
        super().__init__(description, processors, storage, activity=activity, processing_mode=AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN, can_undo=can_undo)
        self.verslagen = verslagen if verslagen else self.__read_verslagen_from_storage()
        self.__sort_verslagen()     
    def __read_verslagen_from_storage(self)->list[Verslag]:
        entry_states = self.processors[0].entry_states
        log_info(f'Start reading verslagen from database. Entry_states: {entry_states}')
        result = self.storage.find_all('verslagen', 
                                       where_attributes='status', 
                                       where_values=entry_states)
        log_info(f'End reading aanvragen from database. {len} aanvragen read.')
        return result
    def __sort_verslagen(self):
        def comparekey(v: Verslag):
            if isinstance(v.datum, datetime.datetime):
                return v.datum
            else:
                return datetime.datetime.now()
        if self.verslagen:
            self.verslagen.sort(key=comparekey, reverse=False) 
    def filtered_verslagen(self, filter_func=None)->list[Verslag]:
        if self.verslagen and filter_func:
            return list(filter(filter_func, self.verslagen))
        else:
            return self.verslagen
    @property
    def processors(self)->list[VerslagProcessor]:
        return self._processors
    def _process_verslag_processor(self, processor: VerslagProcessor, verslag: Verslag, preview=False, **kwargs)->bool:
        try:
            result = (MP:=processor.must_process(verslag, preview=preview, **kwargs)) and processor.process(verslag, preview, **kwargs)                                                
            log_debug(f'_process_verslag_processor: {result}')
            return result
        except Exception as E:
            log_error(f'Fout bij processing verslag ({self.description}) {verslag.summary()}:\n\t{E}')
        log_debug(f'_process_verslag_processor: FALSE')
        return False
    def _process_verslag(self, verslag: Verslag, preview=False, **kwargs)->bool:
        processed = False               
        for processor in self.processors:
            log_debug(ITEM_DEBUG_DIVIDER)
            log_debug(f'processor: {processor.description} [args: {kwargs}]  {processor.must_process(verslag, **kwargs)}')
            if not processor.in_entry_states(verslag.status):
                break
            if self._process_verslag_processor(processor, verslag, preview, **kwargs):
                processed = True
                log_debug(f'processed. Exit state: {processor.exit_state}')
                if processor.exit_state:
                    verslag.status = processor.exit_state                       
                if not processor.read_only:
                    self.storage.update('verslagen', verslag)
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
            if (verslagen := self.filtered_verslagen(filter_func)):
                for verslag in verslagen:
                    log_info(f'Verslag {verslag.summary()}:', to_console=True)
                    if self._process_verslag(verslag, preview, **kwargs):
                        n_processed += 1            
                        self.undo_log_verslag(verslag) 
            self.stop_logging()
            log_debug(MINOR_DEBUG_DIVIDER)
        return n_processed

class VerslagCreatingPipeline(FilePipeline):
    def __init__(self, description: str, processor: VerslagImporter, storage: AAPAStorage, activity: UndoLog.Action):
        super().__init__(description, processor, storage, activity=activity, processing_mode=AAPAProcessingOptions.PROCESSINGMODE.VERSLAGEN, invalid_filetype=None)  
        self.verslag_queries:VerslagenQueries = self.storage.queries('verslagen')
    def _store_new(self, verslag: Verslag):        
        if stored := self.verslag_queries.find_verslag(verslag, config.get('directories', 'error_margin_date')):
            self.storage.update('verslagen', stored)
        else:
            self.storage.create('verslagen', verslag)
        self.undo_log_verslag(verslag)   
    