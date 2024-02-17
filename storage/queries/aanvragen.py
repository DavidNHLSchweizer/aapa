from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from storage.general.CRUDs import CRUDQueries
from database.classes.sql_expr import Ops
from general.timeutil import TSC

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
        return []
    def find_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        self.get_crud(Student).queries.ensure_key(aanvraag.student)        
        self.get_crud(Bedrijf).queries.ensure_key(aanvraag.bedrijf)   
        stored = self.find_values_where('id', where_attributes=['student', 'bedrijf', 'datum_str', 'titel'],
                                        where_values = [aanvraag.student.id, aanvraag.bedrijf.id, 
                                                        TSC.timestamp_to_sortable_str(aanvraag.datum_str), 
                                                        aanvraag.titel])
        if stored:
            return self.crud.read(stored[0]['id'])
        return None
    def find_student_aanvraag(self, student: Student)->Aanvraag:
        if (id := self.find_max_value('id', 'student', student.id)):
            return self.crud.read(id)
        return None
# find_all(where_attributes='status', where_values=Aanvraag.Status.valid_states())


