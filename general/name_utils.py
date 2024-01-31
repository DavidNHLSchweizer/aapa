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
    def _title(name: str)->str:
        def __title(name: str, split_char: str)->str:               
            parts = name.strip().split(split_char)
            result_parts = []
            for part in parts:
                if re.match(Names.TUSSEN_PATTERN, part.lower()):
                    result_parts.append(part.lower())
                else:
                    result_parts.append(part.capitalize())
            return split_char.join(result_parts)       
        if name.find('-') > 0:
            return __title(name, '-')
        else:
            return __title(name, ' ')
    @staticmethod
    def is_tussen(w: str)->bool:
        return re.match(Names.TUSSEN_PATTERN, w, re.IGNORECASE) is not None
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
            return ParsedName(first_name=Names._title(full_name[0:first_tussen_start].strip()), tussen=' '.join(tussens), last_name=Names._title(full_name[last_tussen_end:].strip()))
        else:
            words = full_name.split(' ')
            return ParsedName(first_name=Names._title(' '.join(words[:len(words)-1])), last_name=Names._title(words[len(words)-1]))
    @staticmethod
    def standardize(full_name: str)->str:
        parsed = Names.parsed(full_name)
        result = Names._title(parsed.first_name.strip())
        if parsed.tussen:
            result += f' {parsed.tussen}' 
        return result + f' {Names._title(parsed.last_name.strip())}'
    @staticmethod
    def first_name(full_name: str)->str:
        return Names._title(Names.parsed(full_name).first_name)
    @staticmethod
    def tussen(full_name: str)->str:
        return Names.parsed(full_name).tussen
    @staticmethod
    def last_name(full_name: str, include_tussen: bool=True):
        parsed = Names.parsed(full_name)        
        if include_tussen:
            return f'{parsed.tussen} {Names._title(parsed.last_name)}'
        else:
            return Names._title(parsed.last_name)
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
            return f'{Names._title(first_name.strip())}{" " + tussen if tussen else ""}{" " + Names._title(last)}'
        else:
            return f'{Names._title(first_name.strip())} {Names._title(last_name.strip())}'
