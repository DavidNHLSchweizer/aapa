from typing import Iterable
from data.roots import decode_path, encode_path
from data.AAPdatabase import FilesTableDefinition
from data.classes.files import File
from data.crud.crud_base import CRUDbase
from database.database import Database
from general.keys import get_next_key
from general.log import log_debug
from general.timeutil import TSC

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FilesTableDefinition(), File, no_column_ref_for_key=True)
        self._db_map['filename']['db2obj'] = decode_path
        self._db_map['filename']['obj2db'] = encode_path
        self._db_map['timestamp']['db2obj'] = TSC.str_to_timestamp
        self._db_map['timestamp']['obj2db'] = TSC.timestamp_to_str
        self._db_map['filetype']['db2obj'] = File.Type
    def create(self, file: File):   
        log_debug(f'create: {str(file)}')     
        file.id = get_next_key(FilesTableDefinition.KEY_FOR_ID) #TODO: mogelijk kan dit anders, maar nodig is het niet erg
        super().create(file)
    def read_all(self, file_IDs: Iterable[int])->list[File]:
        return [self.read(id) for id in file_IDs]
    def read_filename(self, filename: str)->File:
        if (rows:=self.database._execute_sql_command(f'select id from {self.table.name} where filename=?', [self.map_object_to_db('filename', filename)],True)):
            return self.read(rows[0][0])
        return None
