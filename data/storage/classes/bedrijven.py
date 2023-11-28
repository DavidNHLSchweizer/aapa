from data.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.storage.table_registry import register_table
from data.storage.storage_base import StorageBase
from database.database import Database

class BedrijvenStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, Bedrijf)   

register_table(class_type=Bedrijf, table=BedrijfTableDefinition(), autoID=True)