""" DetailRec: uniform definition of detail records 

    Maps any detail table (with only [master_id,detail_id]) to a datarecord

    Used for storage.details_crud en storage.extended_crud to read/write any 
    AAPA objects stored in an Aggregator from/to the database
"""
from dataclasses import dataclass
from typing import Type

from data.general.aapa_class import AAPAclass
    
@dataclass
class DetailsRecord:
    """ this is used to read/write the records for all Details tables """
    main_id: int 
    detail_id: int
    class_code: str
    def as_list(self)->list[int|str]:
        return [self.main_id, self.detail_id, self.class_code]
    

