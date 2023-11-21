from typing import Any, Iterable
from data.classes.files import File, Files
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.mappers import ColumnMapper, TableMapper
from data.storage.crud_factory import registerCRUD

from data.storage.milestones import MilestonesStorage
from data.storage.storage_base import StorageCRUD
from data.storage.storage_const import DBtype
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class AanvragenStorage(MilestonesStorage):
    def customize_mapper(self, mapper: TableMapper):
        super().customize_mapper(mapper) #milestone
        mapper.set_mapper(AanvraagStatusColumnMapper('status'))
        mapper.set_mapper(AanvraagBeoordelingColumnMapper('beoordeling'))
    def __load(self, aanvraag_id: int, filetypes: set[File.Type], crud_files: StorageCRUD)->Iterable[File]:
        log_debug('__load')
        params = [aanvraag_id]
        params.extend([ft for ft in filetypes])
        if rows:= self.database._execute_sql_command(f'select id from {crud_files.table.name} where aanvraag_id=? and filetype in (' + ','.join('?'*len(filetypes))+')', params, True):
            file_IDs=[row["id"] for row in rows]
            log_debug(f'found: {file_IDs}')
            result = [crud_files.read(id) for id in file_IDs]
            return result
        return []
    def find_all(self, aanvraag_id: int)->Files:
        log_debug('find_all')
        result = Files(aanvraag_id)        
        filetypes = {ft for ft in File.Type if ft != File.Type.UNKNOWN}
        result.reset_file(filetypes)
        crud = self.get_crud(File)
        if files := self.__load(aanvraag_id, filetypes, crud):
            for file in files:
                result.set_file(file)
        return result        

registerCRUD(class_type=Aanvraag, table=AanvraagTableDefinition(), autoID=True)
