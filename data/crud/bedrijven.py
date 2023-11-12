from data.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.crud.crud_base import CRUDbase
from database.database import Database

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, class_type=Bedrijf, table=BedrijfTableDefinition(), autoID=True)
