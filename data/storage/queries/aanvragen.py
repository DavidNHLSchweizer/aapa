from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.storage.CRUDs import CRUDQueries
from database.sql_expr import Ops

class  AanvraagQueries(CRUDQueries):
    def find_kans(self, student: Student)->int:
        self.get_crud(Student).queries.ensure_key(student)        
        return self.find_count('student', student.id)
    def find_versie(self, student: Student, bedrijf: Bedrijf)->int:
        self.get_crud(Student).queries.ensure_key(student)        
        self.get_crud(Bedrijf).queries.ensure_key(bedrijf)   
        return self.find_max_value(attribute='versie',                                                
                                        where_attributes=['student', 'bedrijf'],
                                        where_values=[student.id, bedrijf.id])     
    def find_previous_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        if aanvraag.versie == 1:
            return None
        self.get_crud(Student).queries.ensure_key(aanvraag.student)
        if result := self.find_values(attributes=['versie', 'student'], 
                                      values=[aanvraag.versie-1, aanvraag.student.id], 
                                      map_values=False):
            return result[0]
        return None
    def find_new_aanvragen(self, first_id: int)->list[Aanvraag]:        
        if rows := self.find_values_where('id', where_attributes=['id', 'status'], where_values=[first_id, Aanvraag.Status.valid_states()], 
                                  where_operators =[Ops.GTE, Ops.IN]):
            return self.crud.read_many({row['id'] for row in rows})
        return None
# find_all(where_attributes='status', where_values=Aanvraag.Status.valid_states())

