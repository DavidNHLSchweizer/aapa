from __future__ import annotations
from dataclasses import dataclass
import datetime
import re
from typing import Tuple

from data.classes.base_dirs import BaseDir

class DirectoryNameParser:
    @dataclass
    class Parsed:
        root: str = ''
        student: str = ''
        datum: datetime.datetime = None
        type: str = ''
    PATTERN1 = r'(?P<root>.*)\\(?P<student>[a-zA-Z\s]+?\,[a-zA-Z\,\s]+)\\(?P<datum>[\d\-]+)\s(beoordelen|beoordeling)\s(?P<type>.+)'
    PATTERN2 = r'(?P<root>.*)\\(?P<student>[a-zA-Z\s]+?\,[a-zA-Z\,\s]+)'
    def __init__(self):
        self.pattern1 = re.compile(DirectoryNameParser.PATTERN1, re.IGNORECASE)
        self.pattern2 = re.compile(DirectoryNameParser.PATTERN2)
    def parsed(self, directory_name: str)->DirectoryNameParser.Parsed:
        def _get_root_and_student(match: re.Match)->Tuple[str,str]:
            return match.group('root'), BaseDir.get_student_name(match.group('student'))
        if (match:=self.pattern1.match(str(directory_name))):
            try:
                root,student=_get_root_and_student(match)
                return DirectoryNameParser.Parsed(root=root.strip(), student=student.strip(), 
                                              datum =datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d'),
                                              type = match.group('type'))
            except ValueError as E:
                print(f'ValueError: {match.group("datum")}: {E}')
                return None
        elif match:=self.pattern2.match(str(directory_name)):
            root,student=_get_root_and_student(match)
            return DirectoryNameParser.Parsed(root=root.strip(), 
                                              student=student.strip())
        return None    
