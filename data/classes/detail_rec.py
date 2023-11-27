from dataclasses import dataclass
from typing import Type

from data.classes.aapa_class import AAPAclass

@dataclass
class DetailRec:
    main_key: int 
    detail_key: int
DetailRecs = list[DetailRec]

@dataclass
class DetailRecData:
    aggregator_name: str
    detail_aggregator_key: str
    detail_rec_type: Type[DetailRec]    
    
