from data.AAPdatabase import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.crud.crud_base import CRUDbaseAuto
from database.database import Database

class CRUD_bedrijven(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition(), Bedrijf)
