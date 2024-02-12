from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from storage.aapa_storage import AAPAStorage
from process.general.base_processor import BaseProcessor, FileProcessor

class AanvraagProcessor(BaseProcessor):
    def __init__(self, entry_states:set[Aanvraag.Status]=None, exit_state:Aanvraag.Status=None, description: str = '', read_only=False):
        self.entry_states = entry_states
        self.exit_state = exit_state
        self.read_only = read_only
        super().__init__(description=description)
    def in_entry_states(self, status:int)->bool:
        if self.entry_states is not None:
            return status in self.entry_states
        else:
            return True
    def must_process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:
        return self.in_entry_states(aanvraag.status)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        return False

class AanvraagCreator(FileProcessor):
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Aanvraag:
        return None
    def is_known_invalid_file(self, filename: str, storage: AAPAStorage, filetype=File.Type.invalid_file_types()):
        return storage.find_values('files', attributes=['filename', 'filetype'], values=[str(filename), filetype], read_many=True) != [] 
