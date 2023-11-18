from typing import Any, Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.studenten import Student
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.mappers import ColumnMapper
from data.crud.crud_const import AAPAClass, DBtype
from data.crud.crud_factory import registerCRUD
from data.crud.files import CRUD_files
from data.crud.milestones import CRUD_milestones
from data.crud.crud_base import CRUD
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class CRUD_aanvragen(CRUD_milestones):
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, 
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def customize_mapper(self):
        super().customize_mapper()
        self.set_mapper(AanvraagStatusColumnMapper('status'))
        self.set_mapper(AanvraagBeoordelingColumnMapper('beoordeling'))
    def _post_action(aanvraag, crud_action):
        match crud_action:
            case CRUD.READ:
                pass # aanvraag.files = self.find_all(aanvraag.id)
            case _: pass
        return aanvraag 
    def __load(self, aanvraag_id: int, filetypes: set[File.Type], crud_files: CRUD_files)->Iterable[File]:
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
        if files := self.__load(aanvraag_id, filetypes, CRUD_files(self.database)):
            for file in files:
                result.set_file(file)
        return result        

registerCRUD(CRUD_aanvragen, class_type=Aanvraag, table=AanvraagTableDefinition(), autoID=True)
