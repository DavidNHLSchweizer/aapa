from __future__ import annotations
from dataclasses import dataclass
from database.dbConst import EMPTY_ID

@dataclass
class Bedrijf:        
    name: str = ''
    id: int = EMPTY_ID #key
    def __str__(self): 
        return f'{self.id}:{self.name}'
    def valid(self):
        return self.name != ''
    def __eq__(self, value: Bedrijf) -> bool:        
        if  self.name != value.name:
            return False
        return True
