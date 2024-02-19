from data.classes.bedrijven import Bedrijf
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
    def find_verslag(self, verslag: Verslag)->Verslag:
        print(f'FIND VERSLAG {verslag}')
        self.get_crud(Student).queries.ensure_key(verslag.student)        
        stored = self.find_values_where('id', where_attributes=['student','datum', 'mijlpaal_type', 'titel'],
                                        where_values = [verslag.student.id, #NOTE: bedrijf kan niet vindbaar zijn voor "oude" verslagen
                                                        TSC.timestamp_to_sortable_str(verslag.datum), 
                                                        verslag.mijlpaal_type,
                                                        verslag.titel])
        if stored:
            print('stoort')
            return self.crud.read(stored[0]['id'])
        print('stoort niet')
        return None
