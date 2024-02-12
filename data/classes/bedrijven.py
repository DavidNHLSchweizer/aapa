from __future__ import annotations
from data.general.aapa_class import AAPAclass
from database.classes.dbConst import EMPTY_ID

class Bedrijf(AAPAclass):        
    def __init__(self, name: str, id = EMPTY_ID):
        super().__init__(id) 
        self.name = name
    def __str__(self): 
        return f'{self.id}:{self.name}'
    def valid(self):
        return self.name != ''
    def __eq__(self, value2: Bedrijf) -> bool:        
        if not value2:
            return False
        if  self.name != value2.name:
            return False
        return True
    def relevant_attributes(self)->set[str]:
        return {'name'}
