from data.general.aapa_class import AAPAclass
from data.general.detail_rec import DetailRec

DBtype = str|int|float
StoredClass = AAPAclass|DetailRec
KeyClass = int|str

class StorageException(Exception): pass

