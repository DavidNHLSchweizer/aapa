""" REMOVE_AANVRAAG.

    Verwijdert 1 of meer aanvragen uit de database.
    Alle gerelateerde records worden ook verwijderd.

"""
from abc import abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalDirectory
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from database.aapa_database import AanvragenTableDefinition, FilesTableDefinition, VerslagenTableDefinition
from database.classes.database import Database
from database.classes.table_def import TableDefinition
from main.log import log_print
from general.sql_coll import SQLcollector, SQLcollectors
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from storage.general.storage_const import StoredClass

class RemoverException(Exception):pass

class RemoverClass:
    def __init__(self, class_type: StoredClass, table_name: str, owner_names: str | list[str], details_id: str = None):
        self.class_type = class_type
        self.table_name = table_name
        if isinstance(owner_names, list):
            self.owner_names = owner_names
        else:
            self.owner_names = [owner_names]
        self.sql = self.init_SQLcollectors()
        self.class_code = ClassCodes.classtype_to_code(class_type)
        self.details_id = details_id
        self._deleted = []
    def _details_name(self)->str:
        return f'{self.table_name.lower()}_details'
    def _add_owned_details(self, sql: SQLcollectors):        
        sql.add(self._details_name(), SQLcollector({'delete':{'sql':f'delete from {self._details_name().upper()} where {self.details_id} in (?)'}, }))
    def _owner_details_name(self, owner: str)->str:
        return f'{owner.lower()}_details'
    def _add_owner_details(self, sql: SQLcollectors, owner: str):
        sql.add(f'{self._owner_details_name(owner)}_details', SQLcollector({'delete':{'sql':f'delete from {self._owner_details_name(owner).upper()}_DETAILS where detail_id=? and class_code=?', 'concatenate': False}, }))
    def init_SQLcollectors(self)->SQLcollectors:
        sql = SQLcollectors()
        sql.add(self.table_name.lower(), SQLcollector({'delete':{'sql':f'delete from {self.table_name.upper()} where id in (?)'}, }))
        for owner in self.owner_names:
            self._add_owner_details(sql, owner)
        if self.details_id:
            self._add_owned_details(sql)
        return sql
    def _delete(self, owner: str, obj: StoredClass):
        self.sql.delete(self._owner_details_name(owner), obj.id, self.class_code)
    def delete(self, obj: StoredClass): 
        for owner in self.owner_names:
            self.delete(owner, obj)        
        self.sql.delete(self.table_name.lower(), obj.id)
        self._deleted.append(obj)
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
        super().__init__(File, 'FILES')
    def init_SQLcollectors(self) -> SQLcollectors:
        return super().init_SQLcollectors(['aanvragen', 'verslagen', 'undologs'])
    def unlink(self, file: File, preview: bool):
        if not preview:
            Path(file.filename).unlink(missing_ok=True)

class MijlpaalRemover(RemoverClass):
    def __init__(self, class_type: MijlpaalDirectory, table_name: str, details_id: str):
        self.file_remover = FileRemover()
        super().__init__(class_type, table_name=table_name, owner_names=['mijlpaal_directories', 'undologs'], details_id=details_id)
    def delete(self, mijlpaal: MijlpaalDirectory):
        for file in mijlpaal.files_list:
            self.file_remover.delete(file)
        super().delete(mijlpaal)
    def remove(self, database: Database, preview: bool):
        self.file_remover.remove(database, preview)
        super().remove(database, preview)

class AanvraagRemover(MijlpaalRemover):
    def __init__(self):
        super().__init__(Aanvraag, table_name='aanvragen', details_id='aanvraag_id')
    
class VerslagRemover(MijlpaalRemover):
    def __init__(self):
        super().__init__(Verslag, table_name='verslagen', details_id='verslag_id')

class MijlpaalDirectoryRemover(RemoverClass):
    def __init__(self):
        self.aanvraag_remover = AanvraagRemover()
        self.verslag_remover = VerslagRemover()
        super().__init__(MijlpaalDirectory, table_name='mijlpaal_directories', owner_names='student_directories', details_id='mp_dir_id')
    def delete(self, mijlpaal_directory: MijlpaalDirectory):
        for aanvraag in mijlpaal_directory.aanvragen:
            self.aanvraag_remover.delete(aanvraag)
        for verslag in mijlpaal_directory.verslagen:
            self.verslag_remover.delete(verslag)
        super().delete(mijlpaal_directory)
    def remove(self, database: Database, preview: bool):
        self.file_remover.remove(database, preview)
        super().remove(database, preview)
