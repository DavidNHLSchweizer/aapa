from argparse import ArgumentParser, Namespace
from data.classes.aanvragen import Aanvraag
from data.storage.aapa_storage import AAPAStorage
from general.log import log_print
from general.sql_coll import SQLcollector, SQLcollectors
from process.aapa_processor.aapa_processor import AAPARunnerContext

EXTRA_DOC = """ 
        REMOVE_AANVRAAG.

        Verwijdert 1 of meer aanvragen uit de database.
        Alle gerelateerde records worden ook verwijderd.

        """
class RemoverException(Exception):pass

class AanvraagRemover:
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.sql = self.init_sql()
    def init_sql(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add('undologs_aanvragen',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_AANVRAGEN where aanvraag_id in (?)'},}))
        sql.add('undologs_files',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_FILES where file_id in (?)'},}))
        sql.add('aanvragen_files', SQLcollector({'delete':{'sql':'delete from AANVRAGEN_FILES where aanvraag_id in (?)'}, }))
        sql.add('files', SQLcollector({'delete':{'sql':'delete from FILES where id in (?)'}, }))                 
        sql.add('aanvragen', SQLcollector({'delete':{'sql':'delete from AANVRAGEN where id in (?)'}, }))
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
            log_print(f'removing aanvraag {id}')
            if not (aanvraag := self.storage.read('aanvragen', id)):
                raise RemoverException(f'Can not read aanvraag {id}')
            self._remove(aanvraag)
        self.sql.execute_sql(self.storage.database, preview)
        self.storage.commit()
        log_print(f'Removed aanvragen {aanvragen_ids}.')

def prog_parser(base_parser: ArgumentParser)->ArgumentParser:
    base_parser.add_argument('--aanvraag', nargs='+', help='Aanvraag id(s) om te verwijderen')
    return base_parser

def extra_action(context:AAPARunnerContext, namespace: Namespace):
    coded_list:str = namespace.aanvraag[0]
    if ',' in coded_list:
        aanvragen = [int(id) for id in coded_list.split(',')]
    else:
        aanvragen = [int(id) for id in coded_list.split()]
    print(f'Aanvragen om te verwijderen: {aanvragen}')
    with context:
        remover = AanvraagRemover(context.configuration.storage)
        remover.remove(aanvragen, context.processing_options.preview)
