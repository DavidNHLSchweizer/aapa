from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.storage.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from data.storage.table_registry import register_table
from data.storage.storage_base import StorageBase
from database.database import Database

class BasedirsTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database:Database=None)->ColumnMapper:
        match column_name:
            case 'directory': return FilenameColumnMapper(column_name)
            case  _: super()._init_column_mapper(column_name, database)
    
class BasedirsStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, BaseDir, autoID=True)   
    def find_base_dir(self, directory: str)->BaseDir:
        return self.find_value('directory', directory)

register_table(class_type=BaseDir, table=BaseDirsTableDefinition(),  mapper_type = BasedirsTableMapper, autoID=True)