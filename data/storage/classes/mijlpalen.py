from data.classes.mijlpalen import Mijlpaal
from data.aapa_database import MijlpaalTableDefinition
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper
from data.storage.CRUDs import register_crud
from data.storage.classes.milestones import MilestonesTableMapper
from database.database import Database

class MijlpalenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Mijlpaal.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Mijlpaal.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
 
register_crud(class_type=Mijlpaal, 
                table=MijlpaalTableDefinition(), 
                mapper_type=MijlpalenTableMapper)
    