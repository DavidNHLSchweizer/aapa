from data.crud.mappers import ColumnMapper, FilenameColumnMapper, TimeColumnMapper
from data.crud.crud_base import CRUD, CRUDbase
from data.crud.crud_const import DBtype
from data.crud.crud_factory import registerCRUD
from data.aapa_database import FilesTableDefinition
from data.classes.files import File

class FileTypeColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->File.Type:
        return File.Type(db_value)

class CRUD_files(CRUDbase):
    def customize_mapper(self):
        self.set_mapper(FilenameColumnMapper('filename'))
        self.set_mapper(TimeColumnMapper('timestamp'))
        self.set_mapper(FileTypeColumnMapper('filetype'))
    def _post_action(self, file: File, crud_action: CRUD)->File:        
        match crud_action:
            case CRUD.INIT:pass
            case _: pass
        return file

registerCRUD(CRUD_files, class_type=File, table=FilesTableDefinition(),autoID=True)#, no_column_ref_for_key=True)