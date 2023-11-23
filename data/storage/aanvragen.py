from typing import Any
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.storage.mappers import ColumnMapper, TableMapper
from data.table_registry import register_table
from data.storage.milestones import MilestonesStorage, MilestonesTableMapper
from data.storage.storage_const import DBtype
from database.database import Database
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class AanvragenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return AanvraagStatusColumnMapper(column_name)
            case 'beoordeling': return AanvraagBeoordelingColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvragenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, Aanvraag)        

register_table(class_type=Aanvraag, table=AanvraagTableDefinition(), mapper_type=AanvragenTableMapper, autoID=True)
