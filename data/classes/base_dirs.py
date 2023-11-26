from dataclasses import dataclass
from pathlib import Path
import re
from data.classes.aapa_class import AAPAclass
from database.dbConst import EMPTY_ID
from general.name_utils import Names

class BaseDir(AAPAclass):
    def __init__(self, year:int, period:str,
                 forms_version:str, directory:str, id=EMPTY_ID):
        super().__init__(id)
        self.year = year
        self.period = period
        self.forms_version = forms_version
        self.directory = directory
    def __str__(self)->str:
        return f'{self.year}-{self.period}: {self.directory}'
    def get_directory_name(self, student_full_name: str)->str:
        parsed = Names.parsed(student_full_name)
        dir_name = f'{parsed.last_name}'
        if parsed.tussen:
            dir_name = dir_name + f', {parsed.tussen}'
        return str(Path(self.directory).joinpath(f'{dir_name}, {parsed.first_name}'))
    @staticmethod
    def get_student_name(path_name: str)->str:
        PATTERN_TUSSEN = r"^(?P<last>[^\,]+)\,(?P<tussen>[^\,]+)\,(?P<first>[^\,]+)$"
        PATTERN_NORMAL = r"^(?P<last>[^\,]+)\,(?P<first>[^\,]+)$"
        path_name = Path(path_name).stem
        if (match:=re.match(PATTERN_TUSSEN, path_name)):
            parts = [match.group("first"), match.group("tussen"), match.group("last")]
        elif (match:=re.match(PATTERN_NORMAL, path_name)):
            parts = [match.group("first"), "", match.group("last")]
        else:
            parts = ['', '', '']
        return ' '.join([part.strip() for part in parts if part])
        