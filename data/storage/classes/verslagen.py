from typing import Any
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from data.storage.general.storage_const import DBtype
from data.storage.table_registry import register_table
from data.storage.classes.milestones import MilestonesStorage, MilestonesTableMapper
from database.database import Database

class VerslagenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)

class VerslagenStorage(MilestonesStorage):pass
    # def __init__(self, database: Database):
    #     super().__init__(database, Verslag)        

register_table(class_type=Verslag, table=VerslagTableDefinition(), crud=VerslagenStorage, mapper_type=VerslagenTableMapper, autoID=True)