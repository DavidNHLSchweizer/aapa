from __future__ import annotations
from dataclasses import dataclass
import datetime
from pathlib import Path
import re

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
        if (match:=self.pattern1.match(str(directory_name))):
            try:
                return DirectoryNameParser.Parsed(root = match.group('root'), student=match.group('student'), 
                                              datum =datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d'),
                                              type = match.group('type'))
            except ValueError as E:
                print(f'ValueError: {match.group("datum")}: {E}')
                return None
        elif match:=self.pattern2.match(str(directory_name)):
            return DirectoryNameParser.Parsed(root = match.group('root'), student=match.group('student'))                                      
        return None    

if __name__=="__main__":   
    def check_student(student_from_directory: str):
        words = []
        for word in student_from_directory.split(','):
            words.insert(0,word.strip())
        first_name = words[0]
        full_name = ' '.join(words)
        return first_name, full_name
    DNP = DirectoryNameParser()
    roots=[ r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024',
            r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023',
            r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022',
            r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021']
    for root in roots:
        print(f'ROOT: {root}')
        for dir in Path(root).rglob('*'):
            if dir.is_dir() and str(dir).find('.git') ==-1 and (info := DNP.parsed(str(dir))):
                print(f'{dir}:\n\t{str(info)}\n\t\t{check_student(info.student)}')

        print(f'-----------------')
