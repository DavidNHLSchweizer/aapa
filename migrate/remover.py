

from data.classes.aanvragen import Aanvraag
from data.storage.aapa_storage import AAPAStorage
from database.database import Database
from general.args import get_options_from_commandline
from migrate.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_config import AAPAConfiguration
from process.aapa_processor.aapa_processor import AAPARunnerContext

class RemoverException(Exception):pass

class AanvraagRemover:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.sql = self.init_sql()
    def init_sql(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add('undologs_aanvragen',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_AANVRAGEN where aanvraag_id = ?'},}))
        sql.add('undologs_files',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_FILES where file_id = ?'},}))
        sql.add('aanvragen_files', SQLcollector({'delete':{'sql':'delete from AANVRAGEN_FILES where aanvraag_id=?'}, }))
        sql.add('files', SQLcollector({'delete':{'sql':'delete from FILES where id=?'}, }))                 
        sql.add('aanvragen', SQLcollector({'delete':{'sql':'delete from AANVRAGEN where id=?'}, }))
        return sql
    def _remove(self, aanvraag: Aanvraag):
        self.sql.delete('undologs_aanvragen', [aanvraag.id])
        self.sql.delete('aanvragen_files', [aanvraag.id])
        for file in aanvraag.files_list:
            self.sql.delete('undologs_files', [file.id])
            self.sql.delete('files', [file.id])
        self.sql.delete('aanvragen', [aanvraag.id])
    def remove(self, aanvraag_id: int|list[int], preview: bool):
        aanvragen_ids = aanvraag_id if isinstance(aanvraag_id, list) else [aanvraag_id]
        for id in aanvragen_ids:
            if not (aanvraag := self.storage.read('aanvragen', id)):
                raise RemoverException(f'Can not read aanvraag {id}')
            self._remove(aanvraag)
        self.sql.execute_sql(self.storage.database, preview)

