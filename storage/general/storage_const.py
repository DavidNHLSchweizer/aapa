from data.general.aapa_class import AAPAclass
from data.general.detail_rec import DetailRec
from data.general.detail_rec2 import DetailRec2

DBtype = str|int|float
StoredClass = AAPAclass|DetailRec|DetailRec2
KeyClass = int|str

class StorageException(Exception): pass

STORAGE_CLASSES='storage.classes'
DATA_CLASSES='data.classes'