from __future__ import annotations
from pathlib import Path
from typing import Iterable
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.action_log import ActionLog
from data.storage.aapa_storage import AAPAStorage
from data.storage.general.storage_const import StoredClass
from general.fileutil import summary_string
from general.log import log_debug, log_error, log_info, log_print, log_warning
from general.preview import Preview
from process.general.base_processor import BaseProcessor, FileProcessor

class PipelineException(Exception): pass
class Pipeline:
    def __init__(self, description: str, processors: BaseProcessor|list[BaseProcessor], 
                 storage: AAPAStorage, activity: ActionLog.Action, can_undo = True):
        self._processors:list[BaseProcessor] = []
        if isinstance(processors, list):
            if not len(processors):
                raise PipelineException('Empty pipeline (no processors)')
            self._processors.extend(processors)
        else:
            self._processors.append(processors)
        self.storage = storage
        self.known_files = self.storage.files.find_all_for_filetype({filetype for filetype in File.Type}-{File.Type.INVALID_PDF, File.Type.UNKNOWN})
        self.action_log = ActionLog(activity, description, can_undo=can_undo)
    @property
    def description(self)->str:
        return self.action_log.description
    def start_logging(self):
        self.action_log.start()
        log_debug(f'STARTING pipeline {self.action_log}')
    def log_aanvraag(self, aanvraag: Aanvraag):
        if aanvraag and aanvraag.status != Aanvraag.Status.DELETED:
            self.action_log.add(aanvraag)
    def stop_logging(self):
        self.action_log.stop()
        log_debug(f'STOPPING aanvragenprocessor {self.action_log}')
        if not self.action_log.is_empty():
            self.storage.action_logs.create(self.action_log)
        self.storage.commit()
    def is_known_file(self, filename: str)->bool: 
        return filename in {file.filename for file in self.known_files} or self.storage.files.is_known_invalid(str(filename))

class FilePipeline(Pipeline):
    def __init__(self, description: str, processors: FileProcessor | list[FileProcessor], storage: AAPAStorage, 
                 activity: ActionLog.Action, invalid_filetype: File.Type=None):
        super().__init__(description, processors, storage, activity=activity)
        self.invalid_file_type = invalid_filetype
        self._invalid_files = []
    def _add_invalid_file(self, filename: str):
        if self.invalid_file_type:
            self._invalid_files.append({'filename': filename, 'filetype': self.invalid_file_type})
    def _skip(self, filename: str)->bool:
        return False
    def _store_new(self, object: StoredClass):
        pass
    @property
    def processors(self)->list[FileProcessor]:
        return self._processors
    def _process_file_processor(self, processor: FileProcessor, filename: str, preview=False, **kwargs)->bool:
        if processor.must_process_file(filename, self.storage, **kwargs):
            try:
                object = processor.process_file(filename, self.storage, preview, **kwargs)
                if object is None:
                    self._add_invalid_file(str(filename))
                    return False
                self._store_new(object)
                self.storage.commit()
                return True
            except Exception as E:
                log_error(f'Fout bij processing file ({self.description}) {summary_string(filename, maxlen=96)}:\n\t{E}')
        return False
    def _process_file(self, filename: Path, preview=False, **kwargs ):
        for processor in self.processors:
            log_debug(f'processor: {processor.__class__} {filename} {kwargs}  {processor.must_process_file(str(filename), self.storage, **kwargs)}')
            if not self._process_file_processor(processor, str(filename), preview, **kwargs):
                log_debug('returning false...')
                return False
        return True
    def _sorted(self, files: Iterable[Path])->Iterable[Path]:
        return files
    def process(self, files: Iterable[Path], preview=False, **kwargs)->tuple[int, int]:
        n_processed = 0
        n_files = 0
        self._invalid_files = []
        with Preview(preview, self.storage, f'process (filepipeline) {self.description}'):
            self.start_logging()
            for filename in self._sorted(files):
                n_files += 1
                if self._skip(filename):
                    continue                    
                if self._process_file(filename, preview, **kwargs):
                    n_processed += 1
            log_debug(f'INVALID_FILES: {len(self._invalid_files)}')
            for entry in self._invalid_files:
                log_debug(f'invalid file: {entry}')
                self.action_log.add(self.storage.files.store_invalid(entry['filename'], entry['filetype']))                
            self.storage.commit()
            self.stop_logging()     
            log_debug(f'end process (f"{self.description}") {n_processed=} {n_files=}')       
        return (n_processed, n_files)

