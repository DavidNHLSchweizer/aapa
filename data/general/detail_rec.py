""" DetailRec: uniform definition of detail records 

    Maps any detail table (with only [master_id,detail_id]) to a datarecord

    Used for storage.details_crud en storage.extended_crud to read/write any 
    AAPA objects stored in an Aggregator from/to the database
"""
from dataclasses import dataclass
from typing import Type

@dataclass
class DetailRec:
    main_key: int 
    detail_key: int
    def as_list(self)->list[int|str]:
        return [self.main_key, self.detail_key]
DetailRecs = list[DetailRec]

@dataclass
class DetailRecData:
    aggregator_name: str
    detail_aggregator_key: str
    detail_rec_type: Type[DetailRec]    
    
