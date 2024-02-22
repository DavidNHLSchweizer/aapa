""" Simple class to generate random students """
import random
from data.classes.studenten import Student
from storage.aapa_storage import AAPAStorage


class RandomStudents:
    def __init__(self, storage: AAPAStorage, status: set[Student.Status]):
        self.storage = storage
        self.students = self._get_students({Student.Status.AANVRAAG, Student.Status.BEZIG})

    def _get_students(self, status: set[Student.Status])->list[Student]:
        if (ids := self.storage.queries('studenten').find_ids_where('status', status)):
            return self.storage.read_many('studenten', set(ids))
        return []    
    def random_student(self)->Student:
        return random.choice(self.students)
        
