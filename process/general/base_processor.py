from __future__ import annotations
from data.classes.files import File
from data.storage.aapa_storage import AAPAStorage
from data.storage.storage_const import StoredClass

class BaseProcessor:
    def __init__(self, description: str = ''):
        self.description = description
    def must_process(self, object: StoredClass, **kwargs)->bool:
        return True
    def process(self, object: StoredClass, preview = False, **kwargs)->bool:
        return False

class FileProcessor(BaseProcessor):
    def __init__(self, description: str = ''):
        super().__init__(description=description)
    def must_process_file(self, filename: str, storage: AAPAStorage, **kwargs)->bool:
        return True
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs):
        return None

