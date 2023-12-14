from __future__ import annotations
from data.classes.aanvragen import Aanvraag
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.base_dirs import BaseDir
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.classes.mijlpalen import Mijlpaal
from database.dbConst import EMPTY_ID


class StudentDirectoryAggregator(Aggregator):
    def __init__(self, owner: StudentDirectory):
        super().__init__(owner=owner)
        self.add_class(Aanvraag, 'aanvragen')
        self.add_class(Mijlpaal, 'mijlpalen')

class StudentDirectory(AAPAclass):
    def __init__(self, student: Student, directory: str, base_dir: BaseDir = None, id: int = EMPTY_ID):
        super().__init__(id)        
        self.student = student
        self.directory = directory
        self.base_dir = base_dir
        self._data = StudentDirectoryAggregator(self)
    @property
    def data(self)->Aggregator:
        return self._data
    @property
    def aanvragen(self)->list[Aanvraag]:
        return self._data.as_list('aanvragen', sort_key=lambda a: a.id, sort_reverse=True)
    @property
    def mijlpalen(self)->list[Mijlpaal]:
        return self._data.as_list('mijlpalen')    
    def add(self, milestone: Milestone):
        if isinstance(milestone, Aanvraag) and self.aanvraag:
            self._data.remove(self.aanvraag)
        self._data.add(milestone)

    