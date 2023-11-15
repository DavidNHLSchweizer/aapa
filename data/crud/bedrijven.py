from data.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.crud.crud_base import CRUDbase
from data.crud.crud_factory import registerCRUD
from database.database import Database

class CRUD_bedrijven(CRUDbase):
    pass

registerCRUD(CRUD_bedrijven, class_type=Bedrijf, table=BedrijfTableDefinition(), autoID=True)