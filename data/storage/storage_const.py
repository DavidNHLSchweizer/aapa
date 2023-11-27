from data.classes.aapa_class import AAPAclass
from data.classes.detail_rec import DetailRec

DBtype = str|int|float
StoredClass = AAPAclass|DetailRec
KeyClass = int|str

class StorageException(Exception): pass

