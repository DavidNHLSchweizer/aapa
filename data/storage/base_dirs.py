from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.mappers import FilenameColumnMapper, TableMapper
from data.storage.crud_factory import registerCRUD
from data.storage.storage_base import StorageBase

class BasedirsStorage(StorageBase):
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_mapper(FilenameColumnMapper('directory'))
    def find_base_dir(self, directory: str)->BaseDir:
        if id := self.searcher.find_id_from_values(attributes=['directory'], values=[directory]):
            return self.read(id)
        return None

registerCRUD(class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)