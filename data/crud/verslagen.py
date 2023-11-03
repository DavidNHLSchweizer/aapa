from data.classes.bedrijven import Bedrijf
from data.classes.verslagen import Verslag
from data.AAPdatabase import VerslagTableDefinition
from data.crud.crud_base import CRUDbaseAuto
from data.crud.studenten import CRUD_studenten
from data.roots import decode_path, encode_path
from database.database import Database
from general.timeutil import TSC

class CRUD_verslagen(CRUDbaseAuto):
    def __init__(self, database: Database):
        super().__init__(database, VerslagTableDefinition(), Verslag)
        self._db_map['stud_nr']['attrib'] = 'student.stud_nr'
        self._db_map['status']['db2obj'] = Verslag.Status
        self._db_map['beoordeling']['db2obj'] = Verslag.Beoordeling
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path
        self._db_map['datum']['db2obj'] = TSC.str_to_timestamp
        self._db_map['datum']['obj2db'] = TSC.timestamp_to_str
    def _read_sub_attrib(self, sub_attrib_name: str, value)->Bedrijf:
        match sub_attrib_name:
            case 'stud_nr': return CRUD_studenten(self.database).read(value)
            case _: return None

