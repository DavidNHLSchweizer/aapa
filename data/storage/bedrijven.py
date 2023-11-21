from data.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.storage.crud_factory import registerCRUD
from data.storage.storage_base import StorageBase

class BedrijvenStorage(StorageBase):
    pass

registerCRUD(class_type=Bedrijf, table=BedrijfTableDefinition(), autoID=True)