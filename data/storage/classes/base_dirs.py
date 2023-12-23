from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.classes.mappers import ColumnMapper, FilenameColumnMapper
from data.storage.general.table_mapper import TableMapper
from data.storage.CRUDs import register_crud
from data.storage.queries.base_dirs import BaseDirQueries
from database.database import Database

class BaseDirsTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database:Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case  _: return super()._init_column_mapper(column_name, database)
    
register_crud(class_type=BaseDir, 
                table=BaseDirsTableDefinition(), 
                mapper_type = BaseDirsTableMapper,
                queries_type=BaseDirQueries
                )