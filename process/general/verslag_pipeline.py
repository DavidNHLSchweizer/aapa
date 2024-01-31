from data.classes.undo_logs import UndoLog
from data.classes.verslagen import Verslag
from data.storage.aapa_storage import AAPAStorage
from process.general.pipeline import FilePipeline
from process.general.verslag_processor import VerslagImporter


class VerslagCreatingPipeline(FilePipeline):
    def __init__(self, description: str, processor: VerslagImporter, storage: AAPAStorage, activity: UndoLog.Action):
        super().__init__(description, processor, storage, activity=activity, invalid_filetype=None)  
    def _store_new(self, verslag: Verslag):
        self.storage.create('verslagen', verslag)
    # self.log_verslag(verslag)
    # def _process_file(self, processor: VerslagCreator, filename: str, preview=False, **kwargs)->bool:
    #     if processor.must_process_file(filename, self.storage, **kwargs):
    #         try:
    #             verslag = processor.process_file(filename, self.storage, preview, **kwargs)
    #             if verslag is None:
    #                 return False
    #             self.storage.verslagen.create(verslag)
    #             self.storage.commit()
    #             # self.log_verslag(verslag)
    #             return True
    #         except Exception as E:
    #             log_error(f'Fout bij processing file ({self.description}) {summary_string(filename, maxlen=96)}:\n\t{E}')
    #     return False    
    # def process(self, files: Iterable[Path], preview=False, **kwargs)->tuple[int, int]:
    #     n_processed = 0
    #     n_files = 0
    #     with Preview(preview, self.storage, 'process (creator)'):
    #         self.start_logging()
    #         for filename in files:
    #             n_files += 1
    #             file_processed = True
    #             for processor in self._processors:
    #                 log_debug(f'processor: {processor.__class__} {filename} {kwargs}  {processor.must_process_file(str(filename), self.storage, **kwargs)}')
    #                 if not self._process_file(processor, str(filename), preview, **kwargs):
    #                     file_processed = False
    #                     break                
    #             if file_processed:
    #                 n_processed += 1
    #         # log_debug(f'INVALID_FILES: {len(self._invalid_files)}')
    #         # for entry in self._invalid_files:
    #         #     log_debug(f'invalid file: {entry}')
    #         #     self.undo_log.add_invalid_file(self.storage.files.store_invalid(entry['filename'], entry['filetype']))                
    #         self.storage.commit()
    #         self.stop_logging()     
    #         log_debug(f'end process (creator) {n_processed=} {n_files=}')       
    #     return (n_processed, n_files)
