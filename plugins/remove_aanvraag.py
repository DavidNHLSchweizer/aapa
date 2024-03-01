""" REMOVE_AANVRAAG.

    Verwijdert 1 of meer aanvragen uit de database.
    Alle gerelateerde records worden ook verwijderd.

"""
from argparse import ArgumentParser
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.general.class_codes import ClassCodes
from main.log import log_print
from general.sql_coll import SQLcollector, SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext

class RemoverException(Exception):pass

class AanvraagRemover(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs) -> bool:
        if not super().before_process(context, **kwdargs):
            return False
        self.sql = self.init_sql()
        self.storage=context.storage
        return True
    def init_sql(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add('undologs_details',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_DETAILS where detail_id=? and class_code=?', 'concatenate': False},}))
        sql.add('aanvragen_details', 
                SQLcollector({'delete':{'sql':f'delete from AANVRAGEN_DETAILS where aanvraag_id in (?)'}, }))       
        sql.add('aanvragen', SQLcollector({'delete':{'sql':'delete from AANVRAGEN where id in (?)'}, }))
        sql.add('mijlpaal_directories_details', SQLcollector({'delete':{'sql':'delete from MIJLPAAL_DIRECTORIES_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
        sql.add('mijlpaal_directories', SQLcollector({'delete':{'sql':'delete from MIJLPAAL_DIRECTORIES where id in (?)'}, }))
        sql.add('student_directories_details', SQLcollector({'delete':{'sql':'delete from STUDENT_DIRECTORIES_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
        sql.add('files', SQLcollector({'delete':{'sql':'delete from FILES where id in (?)'}, }))                 
        return sql
    def _remove(self, aanvraag: Aanvraag):
        self.sql.delete('undologs_details', [aanvraag.id,self.aanvraag_code])
        self.sql.delete('aanvragen_details', [aanvraag.id])
        for file in aanvraag.files_list:
            self.sql.delete('undologs_details', [file.id,self.file_code])
            self.sql.delete('files', [file.id])
        self.sql.delete('mijlpaal_directories_details', [aanvraag.id, self.aanvraag_code])
        self.sql.delete('aanvragen', [aanvraag.id])
    def remove(self, aanvraag_id: int|list[int], preview: bool):
        aanvragen_ids = aanvraag_id if isinstance(aanvraag_id, list) else [aanvraag_id]
        for id in aanvragen_ids:
            if not (aanvraag := self.storage.read('aanvragen', id)):
                raise RemoverException(f'Can not read aanvraag {id}')
            log_print(f'removing aanvraag {id}: {aanvraag}')
            self._remove(aanvraag)
        self.sql.execute_sql(self.storage.database, preview)
        self.storage.commit()
        log_print(f'Removed aanvragen {aanvragen_ids}.')
    def get_parser(self) -> ArgumentParser:
        parser = super().get_parser()
        parser.add_argument('--aanvraag',  type=int, action='append', help='id van aanvra(a)g(en) om te verwijderen. Kan meerdere malen worden ingevoerd : --aanvraag=id1 --aanvraag=id2.')
        return parser
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.aanvraag_code = ClassCodes.classtype_to_code(Aanvraag)
        self.file_code=  ClassCodes.classtype_to_code(File)
        aanvragen = kwdargs.get('aanvraag')
        print(f'Aanvragen om te verwijderen: {aanvragen}')
        self.remove(aanvragen, context.preview)
        return True
