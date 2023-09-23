from data.AAPdatabase import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from database.crud import CRUDbase
from database.database import Database
from general.keys import get_next_key

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition(), Bedrijf)
    def create(self, bedrijf: Bedrijf):
        bedrijf.id = get_next_key(BedrijfTableDefinition.KEY_FOR_ID)
        super().create(bedrijf)   
