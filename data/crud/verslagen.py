from data.classes.bedrijven import Bedrijf
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.crud.crud_base import CRUDbase
from data.crud.studenten import CRUD_studenten
from data.roots import decode_path, encode_path
from database.database import Database
from general.timeutil import TSC

class CRUD_verslagen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, class_type=Verslag, table=VerslagTableDefinition(),  autoID=True)
        # self._db_map['status']['db2obj'] = Verslag.Status
        # self._db_map['beoordeling']['db2obj'] = Verslag.Beoordeling
        self._db_map['directory']['db2obj'] = decode_path
        self._db_map['directory']['obj2db'] = encode_path


