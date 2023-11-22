from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.storage.mappers import FilenameColumnMapper, TableMapper
from data.storage.table_registry import register_table
from data.storage.storage_base import StorageBase
from database.database import Database

class BasedirsStorage(StorageBase):
    def __init__(self, database: Database):
        super().__init__(database, BaseDir, autoID=True)   
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_mapper(FilenameColumnMapper('directory'))
    def find_base_dir(self, directory: str)->BaseDir:
        return self.find_value('directory', directory)

register_table(class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)