import pytest
from database.sql_expr import Ops, SQE

COLUMN1 = 'COLUMN1'
COLUMN2 = 'COLUMN2'
COLUMN3 = 'COLUMN3'
COLUMN4 = 'COLUMN4'
NUMBER1 = 42
NUMBER2 = 42.42
NUMBER3 = 9801
STRING1 = 'tanga'
STRING2 = 'thong'

def test_simple_number():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, NUMBER1)
        assert str(sqe) == f'({COLUMN1} {o} {NUMBER1})'
        assert sqe.parametrized == f'({COLUMN1} {o} ?)'
        assert sqe.parameters == [NUMBER1]
def test_simple_float():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, NUMBER2)
        assert str(sqe) == f'({COLUMN1} {o} {NUMBER2})'
        assert sqe.parametrized == f'({COLUMN1} {o} ?)'
        assert sqe.parameters == [NUMBER2]
def test_simple_number_having():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, NUMBER1, apply=Ops.HAVING, brackets=False)
        assert str(sqe) == f'{Ops.HAVING} ({COLUMN1} {o} {NUMBER1})'
        assert sqe.parametrized == f'{Ops.HAVING} ({COLUMN1} {o} ?)'
        assert sqe.parameters == [NUMBER1]
def test_simple_float_having():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, NUMBER2, apply=Ops.HAVING, brackets=False)
        assert str(sqe) == f'{Ops.HAVING} ({COLUMN1} {o} {NUMBER2})'
        assert sqe.parametrized == f'{Ops.HAVING} ({COLUMN1} {o} ?)'
        assert sqe.parameters == [NUMBER2]
def test_simple_number_nobrackets():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, NUMBER1, brackets=False)
        assert str(sqe) == f'{COLUMN1} {o} {NUMBER1}'
        assert sqe.parametrized == f'{COLUMN1} {o} ?'
        assert sqe.parameters == [NUMBER1]
def test_simple_string():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, STRING1)
        assert str(sqe) == f'({COLUMN1} {o} "{STRING1}")'
        assert sqe.parametrized == f'({COLUMN1} {o} ?)'
        assert sqe.parameters == [STRING1]
def test_simple_in():
    sqe = SQE(COLUMN1, Ops.IN, [NUMBER1, NUMBER2])
    assert str(sqe) == f'({COLUMN1} {Ops.IN} ({NUMBER1},{NUMBER2}))'
    assert sqe.parametrized == f'({COLUMN1} {Ops.IN} (?,?))'
    assert sqe.parameters == [NUMBER1, NUMBER2]


def test_simple_string_having():
    for o in [Ops.EQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, STRING1, apply=Ops.HAVING, brackets=False)
        assert str(sqe) == f'{Ops.HAVING} ({COLUMN1} {o} "{STRING1}")'
        assert sqe.parametrized == f'{Ops.HAVING} ({COLUMN1} {o} ?)'
        assert sqe.parameters == [STRING1]
def test_simple_string_nobrackets():
    for o in [Ops.EQ, Ops.NEQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe = SQE(COLUMN1, o, STRING1, nobrackets=True)
        assert str(sqe) == f'{COLUMN1} {o} "{STRING1}"'
        assert sqe.parametrized == f'{COLUMN1} {o} ?'
        assert sqe.parameters == [STRING1]
def test_compound():
    for o1 in [Ops.EQ, Ops.NEQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
        sqe1 = SQE(COLUMN1, o1, NUMBER1)
        for o2 in [Ops.EQ, Ops.NEQ, Ops.GT, Ops.GTE, Ops.LT, Ops.LTE]:
            sqe2 = SQE(COLUMN2, o2, STRING1)
            for o in [Ops.AND, Ops.OR, Ops.IS, Ops.ISNOT]:
                sqe = SQE(sqe1, o, sqe2)
                assert str(sqe) == f'({str(sqe1)} {o} {str(sqe2)})'
                assert sqe.parametrized == f'(({COLUMN1} {o1} ?) {o} ({COLUMN2} {o2} ?))'
                assert sqe.parameters == [NUMBER1, STRING1]
def test_compound_compound():
    o11 = Ops.EQ
    sqe11 = SQE(COLUMN1, o11, NUMBER1)
    o12 = Ops.NEQ
    sqe12 = SQE(COLUMN2, o12, STRING1)
    o1 = Ops.AND
    sqe1 = SQE(sqe11, o1, sqe12)
    o21 = Ops.LT                    
    sqe21 = SQE(COLUMN3, o21, STRING2)
    o22 = Ops.GT
    sqe22 = SQE(COLUMN4, o22, NUMBER2)
    o2 = Ops.AND
    sqe2 = SQE(sqe21, o2, sqe22)
    o = Ops.OR
    sqe = SQE(sqe1, o, sqe2)
    assert str(sqe) == f'({str(sqe1)} {o} {str(sqe2)})'
    assert sqe.parametrized == f'((({COLUMN1} {o11} ?) {o1} ({COLUMN2} {o12} ?)) {o} (({COLUMN3} {o21} ?) {o2} ({COLUMN4} {o22} ?)))'
    assert sqe.parameters == [NUMBER1, STRING1, STRING2, NUMBER2]
def test_compound_compound_in():
    o11 = Ops.EQ
    sqe11 = SQE(COLUMN1, o11, NUMBER1)
    o12 = Ops.IN
    sqe12 = SQE(COLUMN2, o12, [STRING1,STRING2])
    o1 = Ops.AND
    sqe1 = SQE(sqe11, o1, sqe12)
    o21 = Ops.LT                    
    sqe21 = SQE(COLUMN3, o21, STRING2)
    o22 = Ops.IN
    sqe22 = SQE(COLUMN4, o22, [NUMBER1, NUMBER2, NUMBER3])
    o2 = Ops.AND
    sqe2 = SQE(sqe21, o2, sqe22)
    o = Ops.OR
    sqe = SQE(sqe1, o, sqe2)
    assert str(sqe) == f'({str(sqe1)} {o} {str(sqe2)})'
    assert sqe.parametrized == f'((({COLUMN1} {o11} ?) {o1} ({COLUMN2} {o12} (?,?))) {o} (({COLUMN3} {o21} ?) {o2} ({COLUMN4} {o22} (?,?,?))))'
    assert sqe.parameters == [NUMBER1, STRING1, STRING2, STRING2, NUMBER1,NUMBER2,NUMBER3]
def test_singular_illegal():        
    with pytest.raises(SyntaxError):
        sqe = SQE(None, Ops.NOT, COLUMN1)
def test_singular():
    o1 = Ops.NOT
    o2 = Ops.EQ
    sqe2 = SQE(COLUMN1, o2, STRING1)
    sqe = SQE(None, o1, sqe2)
    assert str(sqe) == f'({o1} {str(sqe2)})'
    assert sqe.parametrized == f'({o1} {sqe2.parametrized})'
    assert sqe.parameters == [STRING1]
