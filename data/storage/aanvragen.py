from typing import Any
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.table_registry import register_table
from data.storage.milestones import MilestonesStorage
from data.storage.storage_const import DBtype
from database.database import Database
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class AanvragenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, Aanvraag)        
    def customize_mapper(self, mapper: TableMapper):
        super().customize_mapper(mapper) #milestone
        mapper.set_mapper(AanvraagStatusColumnMapper('status'))
        mapper.set_mapper(AanvraagBeoordelingColumnMapper('beoordeling'))

register_table(class_type=Aanvraag, table=AanvraagTableDefinition(), autoID=True)
