from typing import Any
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.storage.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from data.storage.storage_const import DBtype
from data.storage.table_registry import register_table
from data.storage.milestones import MilestonesStorage
from database.database import Database


class VerslagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Status(db_value)
class VerslagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Beoordeling(db_value)

class VerslagenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, Verslag)        
    def customize_mapper(self, mapper: TableMapper):
        super().customize_mapper(mapper) #milestones
        mapper.set_mapper(FilenameColumnMapper('directory'))
        mapper.set_mapper(VerslagStatusColumnMapper('status'))
        mapper.set_mapper(VerslagBeoordelingColumnMapper('beoordeling'))

register_table(class_type=Verslag, table=VerslagTableDefinition(), autoID=True)