from __future__ import annotations
from dataclasses import dataclass
import re
# from general.name_utils import Names


special_cases = {'Jan Pieter Klaassen Katrijns':'Jan Pieter||Klaassen Katrijns',
                 'Jan-Pieter Klaassen Katrijns':'Jan-Pieter||Klaassen Katrijns'}



@dataclass
class ParsedName:
    first_name:str=''
    tussen:str=''
    last_name:str=''
    def __eq__(self,p2: ParsedName)->bool:
        return self.first_name==p2.first_name and self.tussen==p2.tussen and self.last_name==p2.last_name

class Names:
    @staticmethod
    def parsed(full_name: str)->ParsedName:
        TUSSEN_PATTERN = r"(?P<tussen>\b(der|den|de|van|ter|te|in\'t|in\s't|in)\b){1,2}?"
        if special_case := special_cases.get(full_name, None):
            words=special_case.split('|')
            print(words)
            return ParsedName(first_name=words[0], tussen=words[1], last_name=words[2])
        match = re.findall(TUSSEN_PATTERN, full_name)
        if match:
            tussen = [m for (m,_) in match]
            # print(tussen)
            # for (m1,_) in match:
            #     print(m1)
            first_part_start = full_name.find(tussen[0])            
            last_part_end = full_name.find(tussen[len(tussen)-1]) + len(tussen[len(tussen)-1])
            return ParsedName(first_name=full_name[0:first_part_start].strip(), tussen=' '.join(tussen), last_name=full_name[last_part_end:].strip())
        else:
            words = full_name.split(' ')
            return ParsedName(first_name=' '.join(words[:len(words)-1]), last_name=words[len(words)-1])
testcases1 = [ 
    {'name': '',  'parsed': ParsedName('', '', '')},
    {'name': 'Jan',  'parsed': ParsedName('', '', 'Jan')},
    {'name': 'Jan Klaassen',  'parsed': ParsedName('Jan', '', 'Klaassen')},]

testcases2 = [ 
    {'name': 'Jan van Klaassen',  'parsed': ParsedName('Jan', 'van', 'Klaassen')},
    {'name': 'Jan van de Klaassen',  'parsed': ParsedName('Jan', 'van de', 'Klaassen')},
    {'name': 'Jan van der Klaassen',  'parsed': ParsedName('Jan', 'van der', 'Klaassen')},
    {'name': 'Jan de Klaassen',  'parsed': ParsedName('Jan', 'de', 'Klaassen')},
    {'name': 'Jan ter Klaassen',  'parsed': ParsedName('Jan', 'ter', 'Klaassen')},
    {'name': "Jan in 't Klaassen",  'parsed': ParsedName('Jan', "in 't", 'Klaassen')},]

testcases3 = [ 
    {'name': 'Jan-Pieter Klaassen',  'parsed': ParsedName('Jan-Pieter', '', 'Klaassen')},
    {'name': 'Jan-Pieter van Klaassen',  'parsed': ParsedName('Jan-Pieter', 'van', 'Klaassen')},
    {'name': 'Jan-Pieter van de Klaassen',  'parsed': ParsedName('Jan-Pieter', 'van de', 'Klaassen')},
    {'name': 'Jan-Pieter van der Klaassen',  'parsed': ParsedName('Jan-Pieter', 'van der', 'Klaassen')},
    {'name': 'Jan-Pieter de Klaassen',  'parsed': ParsedName('Jan-Pieter', 'de', 'Klaassen')},
    {'name': 'Jan-Pieter ter Klaassen',  'parsed': ParsedName('Jan-Pieter', 'ter', 'Klaassen')},
    {'name': "Jan-Pieter in 't Klaassen",  'parsed': ParsedName('Jan-Pieter', "in 't", 'Klaassen')},]

testcases4 = [ 
    {'name': 'Jan Pieter Klaassen',  'parsed': ParsedName('Jan Pieter', '', 'Klaassen')},
    {'name': 'Jan Pieter van Klaassen',  'parsed': ParsedName('Jan Pieter', 'van', 'Klaassen')},
    {'name': 'Jan Pieter van de Klaassen',  'parsed': ParsedName('Jan Pieter', 'van de', 'Klaassen')},
    {'name': 'Jan Pieter van der Klaassen',  'parsed': ParsedName('Jan Pieter', 'van der', 'Klaassen')},
    {'name': 'Jan Pieter de Klaassen',  'parsed': ParsedName('Jan Pieter', 'de', 'Klaassen')},
    {'name': 'Jan Pieter ter Klaassen',  'parsed': ParsedName('Jan Pieter', 'ter', 'Klaassen')},
    {'name': "Jan Pieter in 't Klaassen",  'parsed': ParsedName('Jan Pieter', "in 't", 'Klaassen')},]

testcases5 = [ 
    {'name': 'Jan Pieter Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', '', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter van Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter van de Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van de', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter van der Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van der', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter de Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'de', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter ter Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'ter', 'Klaassen Katrijns')},
    {'name': "Jan Pieter in 't Klaassen Katrijns",  'parsed': ParsedName('Jan Pieter', "in 't", 'Klaassen Katrijns')},]

testcases6 = [ 
    {'name': 'Jan-Pieter Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', '', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter van Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', 'van', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter van de Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', 'van de', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter van der Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', 'van der', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter de Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', 'de', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter ter Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', 'ter', 'Klaassen Katrijns')},
    {'name': "Jan-Pieter in 't Klaassen Katrijns",  'parsed': ParsedName('Jan-Pieter', "in 't", 'Klaassen Katrijns')},]

testcases7 = [ 
    {'name': 'Jan van Klaasvansen',  'parsed': ParsedName('Jan', 'van', 'Klaasvansen')},
    {'name': 'Jan van de Klaassende',  'parsed': ParsedName('Jan', 'van de', 'Klaassende')},
    {'name': 'Jan van der Klaassin',  'parsed': ParsedName('Jan', 'van der', 'Klaassin')},
    {'name': 'Jan de Klaassede',  'parsed': ParsedName('Jan', 'de', 'Klaassede')},
    {'name': 'Jan ter Klaassen',  'parsed': ParsedName('Jan', 'ter', 'Klaassen')},
    {'name': "Jan in 't Klaassen",  'parsed': ParsedName('Jan', "in 't", 'Klaassen')},]


def _test(testcases):
    for testcase in testcases:
        assert Names.parsed(testcase['name']) == testcase['parsed']

def test_testcase_1():
    _test(testcases1)

def test_testcase_2():
    _test(testcases2)    

def test_testcase_3():
    _test(testcases3)        
    
def test_testcase_4():
    _test(testcases4)        
    
def test_testcase_5():
    _test(testcases5)        
    
def test_testcase_6():
    _test(testcases6)        

def test_testcase_7():
    _test(testcases7)        