from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.crud.bedrijven import CRUD_bedrijven
from data.aapa_database import AanvraagTableDefinition, AanvragenViewDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.files import CRUD_files
from data.crud.milestones import CRUD_milestones
from data.crud.crud_base import CRUDbase
from data.crud.studenten import CRUD_studenten
from database.database import Database
from general.timeutil import TSC

class CRUD_aanvragen(CRUDbase):
    def __init__(self, database: Database):        
        super().__init__(database, class_type=Aanvraag, table=AanvraagTableDefinition(), 
                         view=AanvragenViewDefinition(), details=[CRUD_milestones(database)], autoID=True)
        self._db_map['stud_id']['attrib'] = 'student.id'
        self._db_map['bedrijf_id']['attrib'] = 'bedrijf.id'
        self._db_map['source_file_id']['attrib'] = 'source_info.id'
        self._db_map['datum']['db2obj'] = TSC.str_to_timestamp
        self._db_map['datum']['obj2db'] = TSC.timestamp_to_str
    def _read_sub_attrib(self, main_part: str, sub_attrib_name: str, value)->Student|Bedrijf:
        if sub_attrib_name == 'id':
            match main_part:
                case 'student': 
                    return CRUD_studenten(self.database).read(value)
                case 'bedrijf': 
                    return CRUD_bedrijven(self.database).read(value)
                case 'source_info': 
                    return CRUD_files(self.database).read(value)
        return None
    def _post_process(self, aapa_obj: Aanvraag)->Aanvraag:
        #corrects status and beoordeling types (read as ints from database) 
        aapa_obj.status = Aanvraag.Status(aapa_obj.status)
        aapa_obj.beoordeling = Aanvraag.Beoordeling(aapa_obj.beoordeling)
        return aapa_obj 
