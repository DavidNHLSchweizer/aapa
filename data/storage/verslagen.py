from typing import Any
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.storage.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from data.storage.storage_const import DBtype
from data.table_registry import register_table
from data.storage.milestones import MilestonesStorage, MilestonesTableMapper
from database.database import Database

class VerslagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Status(db_value)
class VerslagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Beoordeling(db_value)

class VerslagenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'status': return VerslagStatusColumnMapper(column_name)
            case 'beoordeling': return VerslagBeoordelingColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name)

class VerslagenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, Verslag)        

register_table(class_type=Verslag, table=VerslagTableDefinition(), mapper_type=VerslagenTableMapper, autoID=True)