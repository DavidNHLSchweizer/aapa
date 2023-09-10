import datetime
import os
from pathlib import Path
from typing import Iterable
from data.classes import AanvraagInfo, FileInfo, FileType
from data.storage import AAPStorage
from general.log import log_info, log_print
from general.preview import Preview

class NewAanvraagProcessorBase:
    def must_process(self, aanvraag: AanvraagInfo, **kwargs)->bool:
        return True
    def process(self, aanvraag: AanvraagInfo, preview = False, **kwargs)->bool:
        return False
    def process_file(self, filename: str, storage: AAPStorage, preview = False, **kwargs)->AanvraagInfo:
        return None
    def must_process_file(self, filename: str, storage: AAPStorage, **kwargs)->bool:
        return True

class NewAanvraagProcessor(NewAanvraagProcessorBase):
    def process(self, aanvraag: AanvraagInfo, preview = False, **kwargs)->bool:
        return False

class NewAanvraagFileProcessor(NewAanvraagProcessorBase):
    def process_file(self, filename: str, storage: AAPStorage, preview = False, **kwargs)->AanvraagInfo:
        return None

class NewAanvragenProcessorBase:
    def __init__(self, processors: NewAanvraagProcessorBase|list[NewAanvraagProcessorBase], storage: AAPStorage):
        self._processors:list[NewAanvraagProcessorBase] = []
        if isinstance(processors, list):
            for processor in processors: self._processors.append(processor)
        else:
            self._processors.append(processors)
        self.storage = storage
        self.known_files = self.storage.file_info.find_all_for_filetype({filetype for filetype in FileType})
    def is_known_file(self, filename: str)->bool:        
        return filename in self.known_files

class NewAanvragenProcessor(NewAanvragenProcessorBase):
    def __init__(self, processors: NewAanvraagProcessor|list[NewAanvraagProcessor], storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(processors, storage)
        self.aanvragen = aanvragen if aanvragen else self.__read_from_storage()
        self.__sort_aanvragen() 
    def __read_from_storage(self):
        log_info('Start reading aanvragen from database')
        result = self.storage.aanvragen.read_all()
        log_info('End reading aanvragen from database')
        return result
    def __sort_aanvragen(self):
        def comparekey(a: AanvraagInfo):
            if isinstance(a.timestamp, datetime.datetime):
                return a.timestamp
            else:
                return datetime.datetime.now()
        self.aanvragen.sort(key=comparekey, reverse=True)
    def filtered_aanvragen(self, filter_func=None)->list[AanvraagInfo]:
        if filter_func:
            return list(filter(filter_func, self.aanvragen))
        else:
            return(self.aanvragen)
    def process_aanvragen(self, preview=False, filter_func = None, **kwargs)->int:
        n_processed = 0
        with Preview(preview, self.storage, 'process_aanvragen'):
            for aanvraag in self.filtered_aanvragen(filter_func):
                processed = 0
                for processor in self._processors:
                    # log_print(f'processor: {processor.__class__} {kwargs}  {processor.must_process(aanvraag, **kwargs)}')
                    if processor.must_process(aanvraag, **kwargs) and processor.process(aanvraag, preview, **kwargs):                                                
                        self.storage.aanvragen.update(aanvraag)
                        self.storage.commit()
                        processed+=1
                if processed > 0:
                    n_processed += 1
        return n_processed

class NewAanvragenFileProcessor(NewAanvragenProcessorBase):
    def __init__(self, processors: NewAanvraagProcessorBase|list[NewAanvraagProcessorBase], storage: AAPStorage, skip_directories: set[Path] = {}):
        super().__init__(processors, storage)
        self.skip_directories = skip_directories
    def _in_skip_directory(self, filename: Path)->bool:
        for skip in self.skip_directories:
            if filename.is_relative_to(skip):
                return True
        return False
    def _process_file(self, processor: NewAanvraagFileProcessor, filename: str, storage: AAPStorage, preview=False, **kwargs)->bool:
        if processor.must_process_file(filename, storage, **kwargs):
            aanvraag = processor.process_file(filename, storage, preview, **kwargs)
            if aanvraag is None:
                return False
            self.storage.aanvragen.create(aanvraag)
            self.storage.commit()
            return True
        return False    
    def process_files(self, files: Iterable[Path], preview=False, **kwargs)->int:
        n_processed = 0
        with Preview(preview, self.storage, 'process_files'):
            for filename in sorted(files, key=os.path.getmtime):
                if self._in_skip_directory(filename): 
                    continue
                file_processed = True
                for processor in self._processors:
                    if not self._process_file(processor, str(filename), self.storage, preview, **kwargs):
                        file_processed = False
                        break                
                if file_processed:
                    n_processed += 1
        return n_processed
