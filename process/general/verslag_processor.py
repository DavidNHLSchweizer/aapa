from data.classes.mijlpalen import Mijlpaal
from data.storage.aapa_storage import AAPAStorage
from process.general.base_processor import FileProcessor

class MijlpaalCreator(FileProcessor):
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Mijlpaal:
        return None