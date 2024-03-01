from data.general.aapa_class import AAPAclass
from data.general.details_record import DetailsRecord

DBtype = str|int|float
StoredClass = AAPAclass|DetailsRecord
KeyClass = int|str

class StorageException(Exception): pass

STORAGE_CLASSES='storage.classes'
DATA_CLASSES='data.classes'