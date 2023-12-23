from __future__ import annotations
from data.classes.const import MijlpaalType
from data.classes.mappers import ColumnMapper, FilenameColumnMapper, TimeColumnMapper
from data.storage.general.table_mapper import TableMapper
from data.aapa_database import FilesTableDefinition
from data.classes.files import File
from data.storage.CRUDs import register_crud
from data.storage.queries.files import FilesQueries
from database.database import Database

class FilesTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'filename': return FilenameColumnMapper(column_name)
            case 'timestamp': return TimeColumnMapper(column_name) 
            case 'filetype': return ColumnMapper(column_name=column_name, db_to_obj=File.Type)
            case 'mijlpaal_type': return ColumnMapper(column_name=column_name, db_to_obj=MijlpaalType)
            case _: return super()._init_column_mapper(column_name, database)

register_crud(class_type=File, 
                table=FilesTableDefinition(), 
                mapper_type=FilesTableMapper,
                queries_type=FilesQueries
                )
                