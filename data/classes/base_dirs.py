from __future__ import annotations
from dataclasses import dataclass

from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.config import ListValueConvertor, ValueConvertor, config

class BaseDirConvertor(ValueConvertor):
    def get(self, section_key: str, key_value: str, **kwargs)->YearBase:
        try:
            if (section := self._parser[section_key]) and (value:= section.get(key_value, **kwargs)):
                words = value.split('|')
                return YearBase(words[0], words[1], words[2], words[3])
        except:
            pass
        return None
    def set(self, section_key: str, key_value: str, value: YearBase):
        if (section := self._parser[section_key]) is not None:
            section[key_value] = f'{value.year}|{value.period}|{value.forms_version}|{value.base_dir}'

@dataclass
class YearBase:
    year: int
    period: str
    forms_version: str
    base_dir: str
    id: int = EMPTY_ID
# def init_config():
#     config.register('base_directories', 'years', convertor_class=ListValueConvertor, item_convertor=BaseDirConvertor)
#     config.init('base_directories', 'years', known_bases)
# init_config()

