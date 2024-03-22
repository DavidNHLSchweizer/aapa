""" REMOVER.

    Algemene klassen om aapa-objects uit de database te verwijderen.
    Waar nodig en desgewenst ook uit het filesysteem.
    Alle gerelateerde records worden ook verwijderd.

"""
from pathlib import Path
import shutil
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.classes.mijlpaal_base import MijlpaalGradeable
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.student_directories import StudentDirectory
from data.classes.verslagen import Verslag
from data.general.aapa_class import AAPAclass
from data.general.class_codes import ClassCodes
from data.general.const import MijlpaalType
from database.classes.database import Database
from general.classutil import classname
from general.fileutil import file_exists, test_directory_exists
from general.sql_coll import SQLcollType, SQLcollector, SQLcollectors
from main.log import log_error, log_info, log_print, log_warning
from process.general.preview import pva
from storage.general.storage_const import StoredClass

class RemoverException(Exception):pass

class RemoverClass:
    def __init__(self, class_type: StoredClass, table_name: str, owner_names: tuple[str,str] | list[tuple[str,str]]=None, details_id: str = None, include_owner_in_sql=True):
        self.class_type = class_type
        self.table_name = table_name
        if not owner_names:
            self.owner_names = []
        elif isinstance(owner_names, list):
            self.owner_names = owner_names
        else:
            self.owner_names = [owner_names]
        self.class_code = ClassCodes.classtype_to_code(class_type)
        self.details_id = details_id
        self.sql = self.init_SQLcollectors(include_owner_in_sql=include_owner_in_sql)
        self._deleted = []
        # self._dump_sql()
    # def _dump_sql(self):
    #     print(f'{classname(self)}:')
    #     for ct in SQLcollType:
    #         for collector in self.sql.collectors(ct):
    #                 print(f'{ct}: {collector}')
    def _get_table_references(self, database: Database, table: str, main_id: str, detail_obj: AAPAclass):
        query = f'select distinct {main_id} from {table.upper()}_DETAILS where detail_id=? and class_code=?'
        rows = database._execute_sql_command(query, [detail_obj.id,ClassCodes.classtype_to_code(type(detail_obj))],True)
        return [row[0] for row in rows]
    def get_references(self, database: Database, detail_obj: AAPAclass)->tuple[str,list[int]]:
        """ finds all references to the file in the details tables

            in theory this is always 0 or 1, but the database contains many duplicate references
            
            returns
            -------
            tuple of three lists: (ids in AANVRAGEN_DETAILS, ids in VERSLAGEN_DETAILS, ids in UNDOLOGS_DETAILS)

        """
        return [(owner,self._get_table_references(database, owner, owner_id, detail_obj)) for owner,owner_id in self.owner_names]
        # return (get_table_refs('AANVRAGEN', 'aanvraag_id', file.id), get_table_refs('VERSLAGEN', 'verslag_id', file.id), get_table_refs('UNDOLOGS', 'log_id', file.id))       
    def get_refcount(self,  database: Database, detail_obj: AAPAclass)->int:
        return sum(len(refs) for _,refs in self.get_references(database, detail_obj))
    def _details_name(self)->str:
        return f'{self.table_name.lower()}_details'
    def _add_owned_details(self, sql: SQLcollectors):        
        sql.add(self._details_name(), SQLcollector({'delete':{'sql':f'delete from {self._details_name().upper()} where {self.details_id} in (?)'}, }))
    def _owner_details_name(self, owner: str)->str:
        return f'{owner.lower()}_details'
    def _add_owner_details(self, sql: SQLcollectors, owner: str, owner_id: str=None, include_owner_in_sql=True):
        if owner_id and include_owner_in_sql:    
            sql.add(f'{self._owner_details_name(owner)}', SQLcollector({'delete':{'sql':f'delete from {self._owner_details_name(owner).upper()} where {owner_id}=? and detail_id=? and class_code=?', 'concatenate': False}, }))
        else:
            sql.add(f'{self._owner_details_name(owner)}', SQLcollector({'delete':{'sql':f'delete from {self._owner_details_name(owner).upper()} where detail_id=? and class_code=?', 'concatenate': False}, }))
    def init_SQLcollectors(self, include_owner_in_sql=True)->SQLcollectors:
        sql = SQLcollectors()
        sql.add(self.table_name.lower(), SQLcollector({'delete':{'sql':f'delete from {self.table_name.upper()} where id in (?)'}, }))
        for owner,owner_id in self.owner_names:
            self._add_owner_details(sql, owner, owner_id, include_owner_in_sql=include_owner_in_sql)
        if self.details_id:
            self._add_owned_details(sql)        
        return sql
    def delete(self, obj: StoredClass, owner_id = None): 
        for owner,_ in self.owner_names:
            if owner_id:
                self.sql.delete(self._owner_details_name(owner), [owner_id, obj.id,self.class_code])
            else:
                self.sql.delete(self._owner_details_name(owner), [obj.id,self.class_code])        
        self.sql.delete(self.table_name.lower(), [obj.id])
        self._deleted.append(obj)
    def unlink(self, obj: StoredClass, preview: bool, unlink: bool):
        pass        
    def unlink_directory(self, directory: str|Path, preview: bool, unlink: bool):
        if unlink:
            if not test_directory_exists(directory):
                log_warning(f'Directory {File.display_file(directory)} bestaat niet.')
            else:
                if not preview:
                    shutil.rmtree(directory)
                log_print(f'Directory {File.display_file(directory)} met alle inhoud {pva(preview, 'te verwijderen', 'verwijderd')} van filesysteem.')
    def remove(self, database: Database, preview: bool, unlink: bool):
        for item in self._deleted:
            self.unlink(item, preview, unlink)
        if not self.sql.is_empty():
            log_info(pva(preview, f"Gegenereerde SQL-commando's (wordt niet uitgevoerd op database):", f"Verwijderen uit database"), to_console=True)
            self.sql.execute_sql(database, preview, initial_indent='   ', subsequent_indent='      ')
        if not preview:
            self._deleted = []

class FileRemover(RemoverClass):
    def __init__(self, include_owner_in_sql=True):
        super().__init__(File, 'FILES', owner_names=[('aanvragen', 'aanvraag_id'), ('verslagen','verslag_id'), ('undologs', 'log_id')], include_owner_in_sql=include_owner_in_sql)
    def unlink(self, file: File, preview: bool, unlink: bool):
        if unlink:
            if not file_exists(file.filename):
                log_warning(f'Bestand {File.display_file(file.filename)} bestaat niet (meer).')
            else:
                if not preview:
                    Path(file.filename).unlink(missing_ok=True)
                log_print(f'Bestand {File.display_file(file.filename)} {pva(preview, 'te verwijderen', 'verwijderd')} van filesysteem.')
            
class MijlpaalRemover(RemoverClass):
    def __init__(self, class_type: MijlpaalGradeable, table_name: str, details_id: str, include_owner_in_sql=True):
        self.file_remover = FileRemover(include_owner_in_sql=True)
        super().__init__(class_type, table_name=table_name, owner_names=[('mijlpaal_directories', 'mp_dir_id'), ('undologs', 'log_id')], details_id=details_id, include_owner_in_sql=include_owner_in_sql)
    def delete(self, mijlpaal: MijlpaalGradeable, owner_id: int=None):
        for file in mijlpaal.files_list:
            self.file_remover.delete(file, owner_id=mijlpaal.id)
        super().delete(mijlpaal,owner_id=owner_id)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.file_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)

class AanvraagRemover(MijlpaalRemover):
    def __init__(self, include_owner_in_sql=True):
        super().__init__(Aanvraag, table_name='aanvragen', details_id='aanvraag_id', include_owner_in_sql=include_owner_in_sql)
    
class VerslagRemover(MijlpaalRemover):
    def __init__(self, include_owner_in_sql=True):
        super().__init__(Verslag, table_name='verslagen', details_id='verslag_id', include_owner_in_sql=include_owner_in_sql)

class MijlpaalDirectoryRemover(RemoverClass):
    def __init__(self, include_owner_in_sql=True):
        self.aanvraag_remover = AanvraagRemover()
        self.verslag_remover = VerslagRemover()
        super().__init__(MijlpaalDirectory, table_name='mijlpaal_directories', owner_names=('student_directories','stud_dir_id'), details_id='mp_dir_id', include_owner_in_sql=include_owner_in_sql)
    def delete(self, mijlpaal_directory: MijlpaalDirectory, owner_id: int=None):
        for aanvraag in mijlpaal_directory.aanvragen:
            self.aanvraag_remover.delete(aanvraag,owner_id=mijlpaal_directory.id)
        for verslag in mijlpaal_directory.verslagen:
            self.verslag_remover.delete(verslag,owner_id=mijlpaal_directory.id)
        super().delete(mijlpaal_directory, owner_id=owner_id)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.aanvraag_remover.remove(database, preview, unlink)
        self.verslag_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)
    def unlink(self, mijlpaal_directory: MijlpaalDirectory, preview: bool, unlink: bool):
        if mijlpaal_directory.mijlpaal_type == MijlpaalType.AANVRAAG:
            log_info(f'Directory {File.display_file(mijlpaal_directory.directory)} kan niet worden verwijderd.', to_console=True)
        else:
            self.unlink_directory(mijlpaal_directory.directory, preview, unlink)

class StudentDirectoryRemover(RemoverClass):
    def __init__(self, include_owner_in_sql=False):
        self.mp_dir_remover = MijlpaalDirectoryRemover()
        super().__init__(StudentDirectory, table_name='student_directories', details_id='stud_dir_id', include_owner_in_sql=include_owner_in_sql)
    def delete(self, student_directory: StudentDirectory):
        for directory in student_directory.directories:
            self.mp_dir_remover.delete(directory, student_directory.id)
        super().delete(student_directory)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.mp_dir_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)
    def unlink(self, student_directory: StudentDirectory, preview: bool, unlink):
        self.unlink_directory(student_directory.directory, preview, unlink)

# class StudentRemover(RemoverClass):
            
            #NOTE: tricky, not clear whether this is a good idea

#     def __init__(self):
#         self.stud_dir_remover = StudentDirectoryRemover()
#         super().__init__(Student, table_name='studenten')
#     # def delete(self, student: Student):
#     #     for directory in student_directory.directories:
#     #         self.mp_dir_remover.remove(directory)
#     #     super().delete(student_directory)
#     def find_student_directories(self, storage: AAPAStorage, student: Student)->list[StudentDirectory]:
#         rows = database._execute_sql_command(f'select id from STUDENT_DIRECTORIES where stud_id=?', [student.id], True)