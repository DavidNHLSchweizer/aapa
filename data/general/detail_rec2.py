""" DetailRec: uniform definition of detail records 

    Maps any detail table (with only [master_id,detail_id]) to a datarecord

    Used for storage.details_crud en storage.extended_crud to read/write any 
    AAPA objects stored in an Aggregator from/to the database
"""
from dataclasses import dataclass
from typing import Type

from data.general.aapa_class import AAPAclass
    
@dataclass
class DetailRec2:
    main_id: int 
    detail_id: int
    class_code: str
    def as_list(self)->list[int|str]:
        return [self.main_id, self.detail_id, self.class_code]
DetailRecs2 = list[DetailRec2]

@dataclass
class DetailRecData2:
    aggregator_name: str
    detail_rec_type: Type[DetailRec2]    
    
