from pytest import File
from data.classes.bedrijven import Bedrijf
from data.classes.mijlpaal_directories import MijlpaalDirectory
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from general.timeutil import TSC
from main.log import log_debug
from storage.general.CRUDs import CRUDQueries
from database.classes.sql_expr import Ops

class VerslagQueries(CRUDQueries):
    def find_new_verslagen(self, first_id: int)->list[Verslag]:        
        if rows := self.find_values_where('id', where_attributes=['id', 'status'], where_values=[first_id, Verslag.Status.valid_states()], 
                                  where_operators =[Ops.GTE, Ops.IN]):
            return self.crud.read_many({row['id'] for row in rows})
        return []
    def find_verslag(self, verslag: Verslag, error_margin_date=0)->Verslag:
        self.get_crud(Student).queries.ensure_key(verslag.student)        
        stored = self.find_values_where('id', where_attributes=['student','mijlpaal_type'],
                                        where_values = [verslag.student.id, #NOTE: bedrijf kan niet vindbaar zijn voor "oude" verslagen
                                                        verslag.mijlpaal_type])
                                                        
        if stored:
            results = list(filter(lambda v: TSC.equal_in_range(v.datum, verslag.datum, error_margin_date), self.crud.read_many({row['id'] for row in stored})))
            return results[0] if results else None
        return None
    def find_mp_dir_verslag(self, file: File)->Verslag:
        self.get_crud(MijlpaalDirectory)

