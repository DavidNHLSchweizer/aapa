from data.classes.const import MijlpaalType
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.storage.general.mappers import ColumnMapper, FilenameColumnMapper
from data.storage.CRUDs import register_crud
from data.storage.classes.mijlpaal_base import MijlpaalGradeableTableMapper
from database.database import Database

class VerslagenTableMapper(MijlpaalGradeableTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case 'verslag_type': return ColumnMapper(column_name=column_name, db_to_obj=MijlpaalType)
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
 
register_crud(class_type=Verslag, 
                table=VerslagTableDefinition(), 
                mapper_type=VerslagenTableMapper)
    