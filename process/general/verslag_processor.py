from data.classes.verslagen import Verslag
from data.storage import AAPAStorage
from process.general.base_processor import FileProcessor

class VerslagCreator(FileProcessor):
    def process_file(self, filename: str, storage: AAPAStorage, preview = False, **kwargs)->Verslag:
        return None