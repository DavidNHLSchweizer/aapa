from __future__ import annotations
from dataclasses import dataclass

from data.classes.studenten import Student
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
known_bases = [
               YearBase(2020, '1', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1'),
               YearBase(2020, '1B', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B'),
               YearBase(2020, '2', 'v2.2b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2'),
               YearBase(2021, '1', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1'),
               YearBase(2021, '2', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2'),
               YearBase(2021, '3', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3'),
               YearBase(2021, '4', 'v2.3b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4'),
               YearBase(2022, '1', 'v3.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1'),
               YearBase(2022, '2', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2'),
               YearBase(2022, '3', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3'),
               YearBase(2022, '4', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4'),
               YearBase(2023, '1', 'v4.0.0b', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024'),
]

def init_config():
    config.register('base_directories', 'years', convertor_class=ListValueConvertor, item_convertor=BaseDirConvertor)
    config.init('base_directories', 'years', known_bases)
init_config()

