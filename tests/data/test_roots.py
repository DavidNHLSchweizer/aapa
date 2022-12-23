import pytest

from data.roots import STANDARD_ROOTS, RootException, add_root, decode_path, encode_path, get_roots, reset_roots

def test_standard_roots():
    for i,(_, r) in enumerate(get_roots()):
        assert r == STANDARD_ROOTS[i]


def _test_path(path: str, expected: str):
    p1 = encode_path(path)
    assert p1 == expected
    p2 = decode_path(p1)
    assert p2 == path

TESTCASE =[ {'path':r'C:\test\testing', 'expected':r'C:\test\testing'}, ]

def _test_with_root(path: str):
    expected = add_root(path)
    _test_path(path, expected)

def test_cases():
    for case in TESTCASE:
        _test_path(case['path'], case['expected'])

def test_with_root():
    for case in TESTCASE:
        _test_with_root(case['path'])

def test_duplicate_root():
    NODUP = 'no duplicates please'
    root = add_root(NODUP)
    assert root == add_root(NODUP)

def test_with_code():
    NOGIETS = 'nogiets'
    CODE = 'CODE'
    code = add_root(NOGIETS, CODE)
    assert code == CODE

def test_with_duplicate_code():
    NOGIETS = 'nogietsnogiets'
    CODE = 'CODE2'
    add_root(NOGIETS, CODE)
    with pytest.raises(RootException):
        add_root(NOGIETS+'fiets', CODE)

def test_root_encoding():
    p1 = r'C:\pad1\test'
    code1 = add_root(p1)
    p2 = r'C:\pad1\test\nogeens'
    code2 = add_root(p2)
    assert encode_path(p2) == code2
    assert encode_path(r'C:\pad1\test\nogeens\dinges1')==rf'{code2}\dinges1'