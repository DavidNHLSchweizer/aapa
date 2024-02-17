from data.classes.verslagen import Verslag
from storage.general.CRUDs import CRUDQueries
from database.classes.sql_expr import Ops

class  VerslagQueries(CRUDQueries):
    def find_new_verslagen(self, first_id: int)->list[Verslag]:        
        if rows := self.find_values_where('id', where_attributes=['id', 'status'], where_values=[first_id, Verslag.Status.valid_states()], 
                                  where_operators =[Ops.GTE, Ops.IN]):
            return self.crud.read_many({row['id'] for row in rows})
        return []


