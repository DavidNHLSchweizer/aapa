from __future__ import annotations
from enum import IntEnum
from data.classes.aapa_class import AAPAclass
from database.dbConst import EMPTY_ID
from general.name_utils import Names
from general.valid_email import is_valid_email

class Student(AAPAclass):
    class Status(IntEnum):
        UNKNOWN     = 0
        AANVRAAG    = 1
        BEZIG       = 2
        AFGESTUDEERD= 3 
        GESTOPT     = 10
        def __str__(self):
            STRS = {Student.Status.UNKNOWN: 'nog niet bekend', Student.Status.AANVRAAG: 'aanvraag gedaan',  
                    Student.Status.BEZIG: 'bezig met afstuderen', Student.Status.AFGESTUDEERD: 'afgestudeerd', 
                    Student.Status.GESTOPT: 'gestopt'}
            return STRS[self.value]

    def __init__(self, full_name='', first_name = '', last_name = '', stud_nr='', 
                 email='', status = Status.UNKNOWN, id=EMPTY_ID):        
        super().__init__(id)
        self.full_name = full_name if full_name else Names.full_name(first_name, last_name)
        self.first_name = first_name if first_name else Names.first_name(full_name)
        self.stud_nr = stud_nr
        self.email = email.lower().strip()
        self.status = status
    def __str__(self):
        studnr_part = f'({self.stud_nr})' if self.stud_nr else ''
        return f'{self.full_name}{studnr_part} [{str(self.status)}]'
    def __eq__(self, value: Student):
        if  self.full_name != value.full_name:
            return False
        if  self.stud_nr != value.stud_nr:
            return False
        if  self.email.lower() != value.email.lower():
            return False
        if  self.status != value.status:
            return False
        return True
    def last_name(self):
        return Names.last_name(self.full_name)
    def initials(self)->str:
        return Names.initials(self.full_name, self.email)
    def valid(self)->bool:
        return self.full_name != '' and self.id != EMPTY_ID and self.stud_nr != '' and is_valid_email(self.email) 
    def relevant_attributes(self)->set[str]:
        return {'full_name', 'stud_nr'}

