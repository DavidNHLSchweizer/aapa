import pytest
from database.dbargparser import dbArgParser

class DemoFlags(dbArgParser):
    SINGLE_BOOL     = 1
    SINGLE_STRING   = 2
    SINGLE_NUMBER   = 3
    MULTIPLE_STRING = 4
    flag_map = \
        [{ "flag": SINGLE_BOOL,"attribute":'single_bool', "default":False, "key":'s_bool'},
         { "flag": SINGLE_STRING, "attribute":'single_string', "default":'', "key":'s_string'},
         { "flag": SINGLE_NUMBER, "attribute":'single_number', "default":0, "key":'s_number'},
         { "flag": MULTIPLE_STRING,"attribute":'multiple_string', "default": [], "key":'s_multiple'}
        ]
    def execute(self, flags, target, **args):
        self.parse(flags, target, self.flag_map, **args)

#class ArgParser:
def test_init_bool():
    DF = DemoFlags()
    with pytest.raises(AttributeError):
        assert DF.single_bool == False
def test_init_string():
    DF = DemoFlags()
    with pytest.raises(AttributeError):
        assert DF.single_string == False

def test_init_number():
    DF = DemoFlags()
    with pytest.raises(AttributeError):
        assert DF.single_number == False

def test_init_multiple_string():
    DF = DemoFlags()
    with pytest.raises(AttributeError):
        assert DF.multiple_string == False

def test_single_bool1():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_BOOL], DF)
    assert not DF.single_bool

def test_single_bool2():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_BOOL], DF, s_bool=True)
    assert DF.single_bool

def test_single_string1():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_STRING], DF)
    assert DF.single_string == ''
def test_single_string2():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_STRING], DF, s_string='demo')
    assert DF.single_string == 'demo'
def test_single_number1():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_NUMBER], DF)
    assert DF.single_number == 0
def test_single_number2():
    DF = DemoFlags()    
    DF.execute([DemoFlags.SINGLE_NUMBER], DF, s_number=3.14)
    assert DF.single_number == 3.14
def test_multiple_string1():
    DF = DemoFlags()    
    DF.execute([DemoFlags.MULTIPLE_STRING], DF)
    assert DF.multiple_string == []
def test_multiple_string2a():
    DF = DemoFlags()    
    DF.execute([DemoFlags.MULTIPLE_STRING], DF, s_multiple='1')
    assert DF.multiple_string == ['1']
def test_multiple_string3():
    DF = DemoFlags()    
    DF.execute([DemoFlags.MULTIPLE_STRING], DF, s_multiples=['1','2','3','5'])
    assert DF.multiple_string == ['1','2','3','5']
def test_multiple_string4():
    DF = DemoFlags()    
    DF.execute([DemoFlags.MULTIPLE_STRING], DF, s_multiple=['1','2','3'])
    assert DF.multiple_string == [['1','2','3']]
