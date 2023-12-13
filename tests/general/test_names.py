from general.name_utils import Names, ParsedName, special_cases

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
    {'name': 'Jan Pieter van Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter van de Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van de', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter van der Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'van der', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter de Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'de', 'Klaassen Katrijns')},
    {'name': 'Jan Pieter ter Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', 'ter', 'Klaassen Katrijns')},
    {'name': "Jan Pieter in 't Klaassen Katrijns",  'parsed': ParsedName('Jan Pieter', "in 't", 'Klaassen Katrijns')},]

testcases6 = [ 
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
    {'name': "Jan in 't Klaassen",  'parsed': ParsedName('Jan', "in 't", 'Klaassen')},
    {'name': "Jan-Pieter van Voorst de Tering", 'parsed': ParsedName('Jan-Pieter', "van", 'Voorst de Tering')},
    ]

testcases_special = [ 
    {'name': 'Jan Pieter Klaassen Katrijns',  'parsed': ParsedName('Jan Pieter', '', 'Klaassen Katrijns')},
    {'name': 'Jan-Pieter Klaassen Katrijns',  'parsed': ParsedName('Jan-Pieter', '', 'Klaassen Katrijns')},
    ]

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

def test_testcase_special():
    for entry in testcases_special:
        special_cases.add(entry['name'],entry['parsed'])
    _test(testcases_special)        