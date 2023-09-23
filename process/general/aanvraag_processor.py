from copy import deepcopy
import datetime
import os
from pathlib import Path
import re
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.process_log import ProcessLog
from data.storage import AAPAStorage
from general.fileutil import summary_string
from general.log import log_debug, log_error, log_info, log_print
from general.preview import Preview

class AanvraagProcessorBase:
    def must_process(self, aanvraag: Aanvraag, **kwargs)->bool:
        return True
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        return False
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Aanvraag:
        return None
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:
        return True
    def state_change(self, log: ProcessLog, storage: AAPAStorage, preview = False, **kwargs)->bool: 
        return False

class AanvraagProcessor(AanvraagProcessorBase):
    def file_is_modified(self, aanvraag: Aanvraag, filetype: File.Type):        
        filename = aanvraag.files.get_filename(filetype)
        registered_timestamp = aanvraag.files.get_timestamp(filetype)
        current_timestamp = File.get_timestamp(filename)
        registered_digest  = aanvraag.files.get_digest(filetype)
        current_digest = File.get_digest(filename)        
        return current_timestamp != registered_timestamp or current_digest != registered_digest
        #TODO: Er lijkt wel eens wat mis te gaan bij het opslaan van de digest, maar misschien valt dat mee. Gevolgen lijken mee te vallen.
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        return False

class AanvraagCreator(AanvraagProcessorBase):
    def is_known_invalid_file(self, filename: str, storage: AAPAStorage):
        return storage.files.is_known_invalid(filename)
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Aanvraag:
        return None

class AanvragenProcessorBase:
    def __init__(self, description: str, processors: AanvraagProcessorBase|list[AanvraagProcessorBase], storage: AAPAStorage, activity: ProcessLog.Action):
        self._processors:list[AanvraagProcessorBase] = []
        if isinstance(processors, list):
            for processor in processors: self._processors.append(processor)
        else:
            self._processors.append(processors)
        self.storage = storage
        self.process_log = ProcessLog(activity, description)
        self.known_files = self.storage.files.find_all_for_filetype({filetype for filetype in File.Type})
    def start_logging(self):
        self.process_log.start()
    def log_aanvraag(self, aanvraag: Aanvraag):
        if aanvraag and aanvraag.status != Aanvraag.Status.DELETED:
            self.process_log.add_aanvraag(aanvraag)
    def stop_logging(self):
        self.process_log.stop()
        if not self.process_log.is_empty():
            self.storage.process_log.create(self.process_log)
        self.storage.commit()

    def is_known_file(self, filename: str)->bool: 
        return filename in {file.filename for file in self.known_files} or self.storage.files.is_known_invalid(str(filename))

class AanvragenProcessor(AanvragenProcessorBase):
    def __init__(self, description: str, processors: AanvraagProcessor|list[AanvraagProcessor], storage: AAPAStorage, activity: ProcessLog.Action, aanvragen: list[Aanvraag] = None):
        super().__init__(description, processors, storage, activity=activity)
        self.aanvragen = aanvragen if aanvragen else self.__read_from_storage()
        self.__sort_aanvragen() 
    def __read_from_storage(self):
        log_info('Start reading aanvragen from database')
        result = self.storage.aanvragen.read_all()
        log_info('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: Aanvraag):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        self.aanvragen.sort(key=comparekey, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[Aanvraag]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)
    def _process_aanvraag(self, processor: AanvraagProcessor, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        try:
            if processor.must_process(aanvraag, **kwargs) and processor.process(aanvraag, preview, **kwargs):                                                
                self.storage.aanvragen.update(aanvraag)
                self.storage.commit()
                return True
        except Exception as E:
            log_error(f'Fout bij processing {aanvraag.summary()}:\n\t{E}')
        return False
    def process_aanvragen(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        self.start_logging()
        with Preview(preview, self.storage, 'process_aanvragen'):
            for aanvraag in self.filtered_aanvragen(filter_func):
                processed = 0                
                for processor in self._processors:
                    #log_debug(f'processor: {processor.__class__} {kwargs}  {processor.must_process(aanvraag, **kwargs)}')
                    if self._process_aanvraag(processor, aanvraag, preview, **kwargs):
                        processed += 1
                if processed > 0:
                    n_processed += 1            
                    self.log_aanvraag(aanvraag) 
            self.stop_logging()
        return n_processed

class AanvragenCreator(AanvragenProcessorBase):
    def __init__(self, description: str, processors: AanvraagProcessorBase|list[AanvraagProcessorBase], storage: AAPAStorage, skip_directories: set[Path]={}, skip_files: list[str]=[]):
        super().__init__(description, processors, storage, activity=ProcessLog.Action.CREATE)
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
                log_error(f'Fout bij processing {summary_string(filename, 96)}:\n\t{E}')
        return False    
    def process_files(self, files: Iterable[Path], preview=False, **kwargs)->int:
        n_processed = 0
        with Preview(preview, self.storage, 'process_files'):
            self.start_logging()
            for filename in sorted(files, key=os.path.getmtime):
                if self._in_skip_directory(filename):
                    continue                    
                if self._skip_file(filename) and not self.is_known_file(filename):
                    log_print(f'Overslaan: {summary_string(filename, maxlen=100)}')
                    # if not preview: #kan volgens mij wel weg hier
                    self.storage.files.store_invalid(str(filename))
                    continue
                file_processed = True
                for processor in self._processors:
                    #log_debug(f'processor: {processor.__class__} {filename} {kwargs}  {processor.must_process_file(str(filename), self.storage, **kwargs)}')
                    if not self._process_file(processor, str(filename), preview, **kwargs):
                        file_processed = False
                        break                
                if file_processed:
                    n_processed += 1
            self.stop_logging()            
        return n_processed
