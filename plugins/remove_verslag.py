""" REMOVE_VERSLAG.

    Verwijdert 1 of meer verslagen uit de database.
    Alle gerelateerde records worden ook verwijderd.

"""
from argparse import ArgumentParser
from data.classes.verslagen import Verslag
from main.log import log_print
from general.sql_coll import SQLcollector, SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext

class RemoverException(Exception):pass

class VerslagRemover(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        super().before_process(context, **kwdargs)
        self.sql = self.init_sql()
        self.storage=context.configuration.storage
        return True
    def init_sql(self)->SQLcollectors:
        sql = SQLcollectors()
        # sql.add('undologs_aanvragen',
        #     SQLcollector({'delete':{'sql':'delete from UNDOLOGS_AANVRAGEN where verslag_id in (?)'},}))
        sql.add('undologs_files',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_FILES where file_id in (?)'},}))
        sql.add('verslagen_files', SQLcollector({'delete':{'sql':'delete from VERSLAGEN_FILES where verslag_id in (?)'}, }))
        sql.add('files', SQLcollector({'delete':{'sql':'delete from FILES where id in (?)'}, }))                 
        sql.add('verslagen', SQLcollector({'delete':{'sql':'delete from VERSLAGEN where id in (?)'}, }))
        return sql
    def _remove(self, verslag: Verslag):
        # self.sql.delete('undologs_aanvragen', [Verslag.id])
        self.sql.delete('verslagen_files', [verslag.id])
        for file in verslag.files_list:
            self.sql.delete('undologs_files', [file.id])
            self.sql.delete('files', [file.id])
        self.sql.delete('verslagen', [verslag.id])
    def remove(self, verslag_id: int|list[int], preview: bool):
        verslagen_ids = verslag_id if isinstance(verslag_id, list) else [verslag_id]
        for id in verslagen_ids:
            if not (verslag := self.storage.read('verslagen', id)):
                raise RemoverException(f'Can not read verslag {id}')
            log_print(f'removing verslag {id}: {verslag}')
            self._remove(verslag)
        self.sql.execute_sql(self.storage.database, True)#preview)
        self.storage.commit()
        log_print(f'Removed verslagen {verslagen_ids}.')

    def get_parser(self) -> ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--verslag', type=int, action='append', help='id van verslag(en) om te verwijderen. Kan meerdere malen worden ingevoerd : --verslag=id1 --verslag=id2.')
        return parser
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        verslagen = kwdargs.get('verslag')
        if not verslagen:
            print('Geen verslagen ingevoerd.')
            return False
        print(f'Verslagen om te verwijderen: {verslagen}')
        self.remove(verslagen, context.processing_options.preview)
        return True
