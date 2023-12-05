from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.base_dirs import BaseDir
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.classes.verslagen import Verslag
from database.dbConst import EMPTY_ID


class StudentMilestonesAggregator(Aggregator):
    def __init__(self, owner: StudentMilestones):
        super().__init__(owner=owner)
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(Verslag, 'verslagen')


class StudentMilestones(AAPAclass):
    def __init__(self, student: Student, directory: str, base_dir: BaseDir = None, id: int = EMPTY_ID):
        super().__init__(id)        
        self.student = student
        self.directory = directory
        self.base_dir = base_dir
        self._data = StudentMilestonesAggregator()
    @property
    def aanvraag(self)->Aanvraag:
        if aanvragen := self._data.as_list('aanvragen'):
            return aanvragen[0]
        return None
    @property
    def verslagen(self)->list[Verslag]:
        return self._data.as_list('verslagen')    
    def add(self, milestone: Milestone):
        if isinstance(milestone, Aanvraag) and self.aanvraag:
            self._data.remove(self.aanvraag)
        self._data.add(milestone)

    