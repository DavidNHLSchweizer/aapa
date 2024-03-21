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
from data.general.class_codes import ClassCodes
from database.classes.database import Database
from general.classutil import classname
from general.sql_coll import SQLcollType, SQLcollector, SQLcollectors
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
    def _get_table_references(self, database: Database, table: str, main_id: str, detail_id: int):
        query = f'select distinct {main_id} from {table.upper()}_DETAILS where detail_id=?'
        rows = database._execute_sql_command(query, [detail_id],True)
        return [row[0] for row in rows]
    def get_references(self, database: Database, detail_id: int)->tuple[str,list[int]]:
        """ finds all references to the file in the details tables

            in theory this is always 0 or 1, but the database contains many duplicate references
            
            returns
            -------
            tuple of three lists: (ids in AANVRAGEN_DETAILS, ids in VERSLAGEN_DETAILS, ids in UNDOLOGS_DETAILS)

        """
        return [(owner,self._get_table_references(database, owner, owner_id, detail_id)) for owner,owner_id in self.owner_names]
        # return (get_table_refs('AANVRAGEN', 'aanvraag_id', file.id), get_table_refs('VERSLAGEN', 'verslag_id', file.id), get_table_refs('UNDOLOGS', 'log_id', file.id))       
    def get_refcount(self,  database: Database, detail_id: int)->int:
        return sum(len(refs) for _,refs in self.get_references(database, detail_id))
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
    def remove(self, database: Database, preview: bool, unlink: bool):
        for item in self._deleted:
            self.unlink(item, preview, unlink)
        self.sql.execute_sql(database, preview)
        if not preview:
            self._deleted = []

class FileRemover(RemoverClass):
    def __init__(self, include_owner_in_sql=True):
        super().__init__(File, 'FILES', owner_names=[('aanvragen', 'aanvraag_id'), ('verslagen','verslag_id'), ('undologs', 'log_id')], include_owner_in_sql=include_owner_in_sql)
    def unlink(self, file: File, preview: bool, unlink: bool):
        if not preview and unlink:
            Path(file.filename).unlink(missing_ok=True)
class MijlpaalRemover(RemoverClass):
    def __init__(self, class_type: MijlpaalGradeable, table_name: str, details_id: str, include_owner_in_sql=True):
        self.file_remover = FileRemover(include_owner_in_sql=True)
        super().__init__(class_type, table_name=table_name, owner_names=[('mijlpaal_directories', 'mp_dir_id'), ('undologs', 'log_id')], details_id=details_id, include_owner_in_sql=include_owner_in_sql)
    def delete(self, mijlpaal: MijlpaalGradeable, owner_id: int=None):
        for file in mijlpaal.files_list:
            self.file_remover.delete(file, owner_id=mijlpaal.id)
        super().delete(mijlpaal)
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
    def delete(self, mijlpaal_directory: MijlpaalDirectory):
        for aanvraag in mijlpaal_directory.aanvragen:
            self.aanvraag_remover.delete(aanvraag)
        for verslag in mijlpaal_directory.verslagen:
            self.verslag_remover.delete(verslag)
        super().delete(mijlpaal_directory)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.aanvraag_remover.remove(database, preview, unlink)
        self.verslag_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)
    def unlink(self, mijlpaal_directory: MijlpaalDirectory, preview: bool, unlink: bool):
        if not preview and unlink:
            shutil.rmtree(mijlpaal_directory.directory)

class StudentDirectoryRemover(RemoverClass):
    def __init__(self):
        self.mp_dir_remover = MijlpaalDirectoryRemover()
        super().__init__(StudentDirectory, table_name='student_directories', details_id='stud_dir_id', include_owner_in_sql=False)
    def delete(self, student_directory: StudentDirectory):
        for directory in student_directory.directories:
            self.mp_dir_remover.delete  (directory)
        super().delete(student_directory)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.mp_dir_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)
    def unlink(self, student_directory: StudentDirectory, preview: bool, unlink):
        if not preview and unlink:
            shutil.rmtree(student_directory.directory)

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
