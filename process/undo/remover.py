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
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from data.general.class_codes import ClassCodes
from database.classes.database import Database
from general.classutil import classname
from general.sql_coll import SQLcollType, SQLcollector, SQLcollectors
from storage.aapa_storage import AAPAStorage
from storage.general.storage_const import StoredClass

class RemoverException(Exception):pass

class RemoverClass:
    def __init__(self, class_type: StoredClass, table_name: str, owner_names: str | list[str]=None, details_id: str = None):
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
        self.sql = self.init_SQLcollectors()
        self._deleted = []
        self._dump_sql()
    def _dump_sql(self):
        print(f'{classname(self)}:')
        for ct in SQLcollType:
            for collector in self.sql.collectors(ct):
                    print(f'{ct}: {collector}')
    def _details_name(self)->str:
        return f'{self.table_name.lower()}_details'
    def _add_owned_details(self, sql: SQLcollectors):        
        sql.add(self._details_name(), SQLcollector({'delete':{'sql':f'delete from {self._details_name().upper()} where {self.details_id} in (?)'}, }))
    def _owner_details_name(self, owner: str)->str:
        return f'{owner.lower()}_details'
    def _add_owner_details(self, sql: SQLcollectors, owner: str):
        sql.add(f'{self._owner_details_name(owner)}', SQLcollector({'delete':{'sql':f'delete from {self._owner_details_name(owner).upper()} where detail_id=? and class_code=?', 'concatenate': False}, }))
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
    def __init__(self):
        super().__init__(File, 'FILES', owner_names=['aanvragen', 'verslagen', 'undologs'])
    def unlink(self, file: File, preview: bool, unlink: bool):
        if not preview and unlink:
            Path(file.filename).unlink(missing_ok=True)

class MijlpaalRemover(RemoverClass):
    def __init__(self, class_type: MijlpaalGradeable, table_name: str, details_id: str):
        self.file_remover = FileRemover()
        super().__init__(class_type, table_name=table_name, owner_names=['mijlpaal_directories', 'undologs'], details_id=details_id)
    def delete(self, mijlpaal: MijlpaalGradeable):
        for file in mijlpaal.files_list:
            self.file_remover.delete(file)
        super().delete(mijlpaal)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.file_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)

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
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.aanvraag_remover.remove(database, preview, unlink)
        self.verslag_remover.remove(database, preview, unlink)
        super().remove(database, preview)
    def unlink(self, mijlpaal_directory: MijlpaalDirectory, preview: bool, unlink: bool):
        if not preview and unlink:
            shutil.rmtree(mijlpaal_directory.directory)

class StudentDirectoryRemover(RemoverClass):
    def __init__(self):
        self.mp_dir_remover = MijlpaalDirectoryRemover()
        super().__init__(StudentDirectory, table_name='student_directories', details_id='stud_dir_id')
    def delete(self, student_directory: StudentDirectory):
        for directory in student_directory.directories:
            self.mp_dir_remover.remove(directory)
        super().delete(student_directory)
    def remove(self, database: Database, preview: bool, unlink: bool):
        self.mp_dir_remover.remove(database, preview, unlink)
        super().remove(database, preview, unlink)
    def unlink(self, student_directory: StudentDirectory, preview: bool, unlink):
        if not preview and unlink:
            shutil.rmtree(student_directory.directory)

# class StudentRemover(RemoverClass):
            #NOTE: tricky, not clear. 
#     def __init__(self):
#         self.stud_dir_remover = StudentDirectoryRemover()
#         super().__init__(Student, table_name='studenten')
#     # def delete(self, student: Student):
#     #     for directory in student_directory.directories:
#     #         self.mp_dir_remover.remove(directory)
#     #     super().delete(student_directory)
#     def find_student_directories(self, storage: AAPAStorage, student: Student)->list[StudentDirectory]:
#         rows = database._execute_sql_command(f'select id from STUDENT_DIRECTORIES where stud_id=?', [student.id], True)
