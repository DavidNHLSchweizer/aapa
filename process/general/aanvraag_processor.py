from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.storage import AAPAStorage

class AanvraagProcessorBase:
    def __init__(self, entry_states: set[Aanvraag.Status] = None, exit_state: Aanvraag.Status = None, description: str = ''):
        self.entry_states = entry_states
        self.exit_state = exit_state
        self.description = description
    def in_entry_states(self, status: Aanvraag.Status)->bool:
        if self.entry_states is not None:
            return status in self.entry_states
        else:
            return True

class AanvraagProcessor(AanvraagProcessorBase):
    def must_process(self, aanvraag: Aanvraag, **kwargs)->bool:
        return self.in_entry_states(aanvraag.status)
    def process(self, aanvraag: Aanvraag, preview = False, **kwargs)->bool:
        return False

class AanvraagCreator(AanvraagProcessorBase):
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:
        return True
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Aanvraag:
        return None
    def is_known_invalid_file(self, filename: str, storage: AAPAStorage):
        return storage.files.is_known_invalid(filename)

