""" REMOVE_AANVRAAG.

    Verwijdert 1 of meer aanvragen uit de database.
    Alle gerelateerde records worden ook verwijderd.

"""
from abc import abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.general.class_codes import ClassCodes
from database.aapa_database import AanvragenTableDefinition, FilesTableDefinition
from database.classes.database import Database
from database.classes.table_def import TableDefinition
from main.log import log_print
from general.sql_coll import SQLcollector, SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.general.storage_const import StoredClass

class RemoverException(Exception):pass


class RemoverClass:
    def __init__(self, class_type: StoredClass, table: TableDefinition):
        self.class_type = class_type
        self.table = table
        self.sql = self.init_SQLcollectors()
        self._deleted = []
    def init_SQLcollectors(self)->SQLcollectors:
        return SQLcollectors()
    @abstractmethod
    def delete(self, obj: StoredClass): 
        pass
    def unlink(self, obj: StoredClass, preview: bool):
        pass        
    def remove(self, database: Database, preview: bool):
        for item in self._deleted:
            self.unlink(item, preview)
        self.sql.execute_sql(database, preview)
        if not preview:
            self._deleted = []

class FileRemover(RemoverClass):
    def __init__(self):
        super().__init__(File, FilesTableDefinition())
        self.file_code = ClassCodes.classtype_to_code(File)
    def init_SQLcollectors(self) -> SQLcollectors:
        result = super().init_SQLcollectors()
        result.add('files', SQLcollector({'delete':{'sql':f'delete from {self.table.name} where id in (?)'}, }))
        result.add('aanvragen_details', SQLcollector({'delete':{'sql':f'delete from AANVRAGEN_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
        result.add('verslagen_details', SQLcollector({'delete':{'sql':f'delete from VERSLAGEN_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
        result.add('undologs_details', SQLcollector({'delete':{'sql':f'delete from UNDOLOGS_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
        return result
    def delete(self, file: File):
        self.sql.delete('aanvragen_details', file.id, self.file_code)
        self.sql.delete('verslagen_details', file.id, self.file_code)
        self.sql.delete('undologs_details', file.id, self.file_code)
        self.sql.delete('files', file.id)
        self._deleted.append(file)
    def unlink(self, file: File, preview: bool):
        if not preview:
            Path(file.filename).unlink(missing_ok=True)
          
class AanvraagRemover(RemoverClass):
    def __init__(self):
        super().__init__(Aanvraag, AanvragenTableDefinition())
        self.file_remover = FileRemover()
        self.aanvraag_code = ClassCodes.classtype_to_code(Aanvraag)
    def init_sql(self)->SQLcollectors:
        result = super().init_SQLcollectors()
        result.add('undologs_details',
            SQLcollector({'delete':{'sql':'delete from UNDOLOGS_DETAILS where detail_id=? and class_code=?', 'concatenate': False},}))
        result.add('mijlpaal_directories_details', 
                SQLcollector({'delete':{'sql':f'delete from MJILPAAL_DIRECTORIES_DETAILS where aanvraag_id = ? and class_code=?','concatenate': False}, }))
        result.add('aanvragen_details', SQLcollector({'delete':{'sql':f'delete from AANVRAGEN_DETAILS where id in (?)'}, }))
        result.add('aanvragen', SQLcollector({'delete':{'sql':f'delete from {self.table.name} where id in (?)'}, }))
        return result
    def delete(self, aanvraag: Aanvraag):
        self.sql.delete('undologs_details', [aanvraag.id,self.aanvraag_code])
        self.sql.delete('mijlpaal_directories_details', [aanvraag.id,self.aanvraag_code])
        self.sql.delete('aanvragen_details', [aanvraag.id])
        for file in aanvraag.files_list:
            self.file_remover.delete(file)
        self.sql.delete('aanvragen', [aanvraag.id])
        self._deleted.append(aanvraag)
    def remove(self, database: Database, preview: bool):
        self.file_remover.remove(database, preview)
        super().remove(database, preview)
    
    
    
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
