from __future__ import annotations
from dataclasses import dataclass
import datetime
import re

from general.config import config

class FilenameInZipParser:
    @dataclass
    class Parsed:
        product_type: str
        kans: str
        email: str
        datum: datetime.datetime
        original_filename: str
        @property
        def student_name(self)->str:
            words = []         
            tussen_voegsels = config.get('names', 'tussen')   
            for word in self.email[:self.email.find('@')].split('.'):
                if word in tussen_voegsels:
                    words.append(word)
                else:
                    words.append(word.title())
            return ' '.join(words)
    PATTERN = r'Inleveren\s+(?P<product_type>.+)\s+\((?P<kans>.+)\)_(?P<email>.+)_poging_(?P<datum>[\d\-]+)_(?P<filename>.+)'
    def __init__(self):
        self.pattern = re.compile(FilenameInZipParser.PATTERN)
    def parsed(self, filename: str)->FilenameInZipParser.Parsed:
        if (match:=self.pattern.match(str(filename))):
            return FilenameInZipParser.Parsed(product_type=match.group('product_type'), kans=match.group('kans'), 
                                  email=match.group('email'), 
                                  datum=datetime.datetime.strptime(match.group('datum'),'%Y-%m-%d-%H-%M-%S'),
                                  original_filename=match.group('filename'))
        return None