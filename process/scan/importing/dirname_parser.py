from __future__ import annotations
from dataclasses import dataclass
import datetime
import re
from typing import Tuple

from data.classes.base_dirs import BaseDir
from general.fileutil import summary_string
from general.log import log_warning

class DirectoryNameParser:
    @dataclass
    class Parsed:
        root: str = ''
        student: str = ''
        datum: datetime.datetime = None
        type: str = ''
    STANDARD_PATTERN = r'(?P<root>.*)\\(?P<student>[a-zA-Z\s]+?\,[a-zA-Z\,\s]+)\\(?P<datum>[\d\-]+)\s(?P<what>.+)'
    PATTERN_BEOORDELING = r'((beoordelen|beoordeling)\s)?(?P<type>.+)'
    PATTERN_NON_STANDARD = r'(?P<rest1>.*)?(?P<part>(PVA|Plan van aanpak|Onderzoeksverslag|Technisch verslag|Eindverslag|Afstudeerzitting))(?P<rest2>.*)?'
    PATTERN_ROOT = r'(?P<root>.*)\\(?P<student>[a-zA-Z\s]+?\,[a-zA-Z\,\s]+)'
    def __init__(self):
        self.standard_pattern = re.compile(self.STANDARD_PATTERN, re.IGNORECASE)
        self.pattern_beoordeling = re.compile(self.PATTERN_BEOORDELING, re.IGNORECASE)
        self.pattern_non_standard = re.compile(DirectoryNameParser.PATTERN_NON_STANDARD, re.IGNORECASE)
        self.pattern_root = re.compile(DirectoryNameParser.PATTERN_ROOT)
    def parse_non_standard(self, directory_name: str, directory_part: str)->str:
        if match := self.pattern_non_standard.match(directory_part):
            type_str = match.group('part')
            log_warning(f'Niet-standaard naamgeving in directory {summary_string(directory_name, maxlen=80)}\n'+
                        f'\twordt geinterpreteerd als {type_str}'
                        )
            return type_str
        return ''
    def parsed(self, directory_name: str)->DirectoryNameParser.Parsed:
        def _get_root_and_student(match: re.Match)->Tuple[str,str]:
            return match.group('root'), BaseDir.get_student_name(match.group('student'))
        if (match:=self.standard_pattern.match(str(directory_name))):
            try:
                root,student=_get_root_and_student(match)
                if match2:=self.pattern_beoordeling.match(match.group('what')):
                    type_str = match2.group('type').strip()
                else:
                    type_str = match.group('what').strip()
                return DirectoryNameParser.Parsed(root=root.strip(), student=student.strip(), 
                                              datum =datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d'),
                                              type = type_str)
            except ValueError as E:
                print(f'ValueError: {match.group("datum")}: {E}')
                return None
        # elif (match:=self.pattern_zitting.match(str(directory_name))):
        #     try:
        #         root,student=_get_root_and_student(match)
        #         return DirectoryNameParser.Parsed(root=root.strip(), student=student.strip(), 
        #                                       datum =datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d'),
        #                                       type = 'afstudeerzitting')
        #     except ValueError as E:
        #         print(f'ValueError: {match.group("datum")}: {E}')
        #         return None
        elif match:=self.pattern_root.match(str(directory_name)):
            root,student=_get_root_and_student(match)
            return DirectoryNameParser.Parsed(root=root.strip(), student=student.strip())
        return None    
