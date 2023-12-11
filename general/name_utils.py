from __future__ import annotations
from dataclasses import dataclass
import re
from general.config import config
from general.singleton import Singleton

@dataclass
class ParsedName:
    first_name:str=''
    tussen:str=''
    last_name:str=''    
    def serialize(self)->str:
        return f'{self.first_name}|{self.tussen}|{self.last_name}'
    @staticmethod
    def deserialize(value: str)->ParsedName:
        words = value.split('|')
        return ParsedName(first_name=words[0], tussen=words[1], last_name=words[2])
    def __eq__(self,p2: ParsedName)->bool:
        return self.first_name==p2.first_name and self.tussen==p2.tussen and self.last_name==p2.last_name

class SpecialCases(Singleton):
    def __init__(self):
        self._cases = {}
    def add(self, full_name: str, parsed: ParsedName):
        self._cases[full_name.lower()] = parsed
    def contains(self, full_name: str)->bool:
        return full_name.lower() in self._cases
    def parsed_name(self, full_name: str)->ParsedName:
        return self._cases.get(full_name.lower(), None)
    def load_from_config(self):
        try:            
            for special_name,value in config.items('special_names'):
                self.add(special_name, ParsedName.deserialize(value))
        except:
            pass
    def save_to_config(self):
        for special_name, parsed in self._cases.items():
            config.set('special_names', special_name, parsed.serialize())
special_cases = SpecialCases()

def init_special_cases():
    special_cases.load_from_config()
    special_cases.add('Rob Klein Ikink', ParsedName('Rob', '', 'Klein Ikink'))
    special_cases.save_to_config()
init_special_cases()

class Names:
    TUSSEN_PATTERN = r"(?P<tussen>\b(der|den|de|van|ter|te|in\'t|in\s't|in)\b)+?"
    @staticmethod
    def parsed(full_name: str)->ParsedName:
        if special_cases.contains(full_name):
            return special_cases.parsed_name(full_name)
        first_tussen_start = -1
        last_tussen_end = -1        
        tussens = []
        for match in re.finditer(Names.TUSSEN_PATTERN, full_name):
            tussen_start = match.start('tussen')
            if tussen_start > last_tussen_end and full_name[last_tussen_end:tussen_start].strip(): # catch extreme case like "van Voorst de Water"
                break
            if first_tussen_start == -1:
                first_tussen_start = tussen_start
            tussens.append(match.group('tussen'))
            last_tussen_end = match.end('tussen')
        if tussens:
            return ParsedName(first_name=full_name[0:first_tussen_start].strip(), tussen=' '.join(tussens), last_name=full_name[last_tussen_end:].strip())
        else:
            words = full_name.split(' ')
            return ParsedName(first_name=' '.join(words[:len(words)-1]), last_name=words[len(words)-1])
    @staticmethod
    def first_name(full_name: str)->str:
        return Names.parsed(full_name).first_name
    @staticmethod
    def tussen(full_name: str)->str:
        return Names.parsed(full_name).tussen
    @staticmethod
    def last_name(full_name: str, include_tussen: bool=True):
        parsed = Names.parsed(full_name)        
        if include_tussen:
            return f'{parsed.tussen} {parsed.last_name}'
        else:
            return parsed.last_name
    @staticmethod
    def initials(full_name: str='', email: str = '')->str:
        result = ''
        if email:
            for word in email[:email.find('@')].split('.'):
                result += word[0]
        elif full_name:            
            for word in full_name.split(' '):
                result += word[0]
        return result.lower()
    @staticmethod
    def full_name(first_name: str, last_name: str)->str:
        if last_name.find(',') != -1:
            parsed = Names.parsed(last_name.strip())
            tussen = parsed.tussen
            last = last_name.strip() if not tussen else last_name[:last_name.find(',')].strip()
            return f'{first_name.strip()}{" " + tussen if tussen else ""}{" " + last}'
        else:
            return f'{first_name.strip()} {last_name.strip()}'
