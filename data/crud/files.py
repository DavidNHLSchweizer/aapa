from data.crud.adapters import ColumnAdapter, FilenameColumnAdapter, TimeColumnAdapter
from data.crud.crud_base import CRUD, CRUDbase
from data.crud.crud_const import DBtype
from data.crud.crud_factory import registerCRUD
from data.roots import decode_path, encode_path
from data.aapa_database import FilesTableDefinition
from data.classes.files import File
from general.timeutil import TSC


class FileTypeColumnAdapter(ColumnAdapter):
    def map_db_to_value(self, db_value: DBtype)->File.Type:
        return File.Type(db_value)

class CRUD_files(CRUDbase):
    def _post_action(self, file: File, crud_action: CRUD)->File:        
        match crud_action:
            case CRUD.INIT:
                self.adapter.set_adapter(FilenameColumnAdapter('filename'))
                self.adapter.set_adapter(TimeColumnAdapter('timestamp'))
                self.adapter.set_adapter(FileTypeColumnAdapter('filetype'))
            case _: pass
        return file

registerCRUD(CRUD_files, class_type=File, table=FilesTableDefinition(),autoID=True)#, no_column_ref_for_key=True)