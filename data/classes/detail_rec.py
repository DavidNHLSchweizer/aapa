from dataclasses import dataclass

from data.classes.aapa_class import AAPAclass



@dataclass
class DetailRec:
    main_key: int 
    detail_key: int
DetailRecs = list[DetailRec]

@dataclass
class DetailRecData:
    main_class: AAPAclass
    main_key_name: str
    detail_class: AAPAclass
    detail_key_name: str
    