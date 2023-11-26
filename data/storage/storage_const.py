from dataclasses import dataclass
from data.classes.aapa_class import AAPAclass

DBtype = str|int|float

@dataclass
class DetailRec:
    main_key: int 
    detail_key: int
DetailRecs = list[DetailRec]

AAPAClass = AAPAclass|DetailRec
KeyClass = int|str
