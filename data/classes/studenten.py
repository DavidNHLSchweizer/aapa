from __future__ import annotations
from database.dbConst import EMPTY_ID
from general.valid_email import is_valid_email

class Student:
    def __init__(self, full_name='', first_name = '', stud_nr='', tel_nr='', email='', id=EMPTY_ID):        
        self.id = id
        self.full_name = full_name
        self.first_name = first_name if first_name else self._get_first_name()
        self.stud_nr = stud_nr
        self.tel_nr = tel_nr
        self.email = email
    def __str__(self):
        return f'{self.full_name}({self.stud_nr})'
    def __eq__(self, value: Student):
        if  self.full_name != value.full_name:
            return False
        if  self.stud_nr != value.stud_nr:
            return False
        if  self.tel_nr != value.tel_nr:
            return False
        if  self.email != value.email:
            return False
        return True
    def _get_first_name(self):
        if self.full_name and (words := self.full_name.split(' ')):
            return words[0]
        return ''
    def initials(self)->str:
        result = ''
        if self.email:
            for word in self.email[:self.email.find('@')].split('.'):
                result = result + word[0]
        return result 
    def valid(self)->bool:
        return self.full_name != '' and self.id != EMPTY_ID and self.stud_nr != '' and is_valid_email(self.email) 

