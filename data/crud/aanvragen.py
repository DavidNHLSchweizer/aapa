from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.crud_factory import registerCRUD
from data.crud.files import CRUD_files
from data.crud.milestones import CRUD_milestones
from data.crud.crud_base import AAPAClass, CRUDbase
from data.crud.studenten import CRUD_studenten
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug
from general.timeutil import TSC

class CRUD_aanvragen(CRUD_milestones):
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, 
                    superclass_CRUDs: list[CRUDbase] = [], subclass_CRUDs:dict[str, AAPAClass]={}, 
                    no_column_ref_for_key = False, autoID=False):
        super().__init__(database, class_type=class_type, table=table, superclass_CRUDs=superclass_CRUDs, subclass_CRUDs=subclass_CRUDs,
                         no_column_ref_for_key=no_column_ref_for_key, autoID=autoID)        
    def _after_init(self): pass
        # self._db_map['stud_id']['attrib'] = 'student.id'
        # self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        # # self._db_map['source_file_id']['attrib'] = 'source_info.id'
        # self._db_map['datum']['db2obj'] = TSC.str_to_timestamp
        # self._db_map['datum']['obj2db'] = TSC.timestamp_to_str
    # def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->Student|Bedrijf:
    #     if sub_attrib_name == 'id':
    #         match main_part:
    #             # case 'student': 
    #             #     return CRUD_studenten(self.database).read(value)
    #             # case 'bedrijf': 
    #             #     return CRUD_bedrijven(self.database).read(value)
    #             case 'source_info': 
    #                 return CRUD_files(self.database).read(value)
    #     return None
    def _post_process_read(self, aanvraag: Aanvraag)->Aanvraag:
        #corrects status and beoordeling types (read as ints from database) 
        # aanvraag.status = Aanvraag.Status(aanvraag.status)
        # aanvraag.beoordeling = Aanvraag.Beoordeling(aanvraag.beoordeling)
        aanvraag.files = self.find_all(aanvraag.id)
        print('pos t process -read- doe iets')
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

registerCRUD(CRUD_aanvragen, class_type=Aanvraag, table=AanvraagTableDefinition(), 
            superclasses=[Milestone], subclasses={'student': Student, 'bedrijf': Bedrijf}, autoID=True)
