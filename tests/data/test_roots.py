from pathlib import Path
from data.roots import BASEPATH, OneDriveCoder, add_root, decode_path, encode_path, get_code, get_expanded, get_onedrive_root, get_roots, reset_roots, set_onedrive_root

onedrive_root = get_onedrive_root()
onedrive_base = onedrive_root.joinpath(BASEPATH)

def test_root1():
    assert encode_path(onedrive_base) == ':ROOT1:'

def test_root1_code():
    expected = Path(OneDriveCoder.ONEDRIVE).joinpath(BASEPATH)
    assert get_code(':ROOT1:') == str(expected)

def test_decode_root1():
    assert decode_path(':ROOT1:') == str(onedrive_base)

def test_encode_file():
    hallo = onedrive_base.joinpath('hallo')
    assert encode_path(hallo) == rf':ROOT1:\hallo'

def test_decode_encode_file():
    hallo = onedrive_base.joinpath('hallo')
    assert decode_path(encode_path(hallo)) == str(hallo)

def test_add():
    hallo = onedrive_base.joinpath('hallo')
    new_code = add_root(hallo)
    assert new_code == ':ROOT2:'
    assert get_code(new_code) == rf':ROOT1:\hallo'
    assert encode_path(hallo) == new_code
    assert encode_path(hallo.joinpath('goodbye')) == rf':ROOT2:\goodbye'

def test_reset():
    test_root1()
    assert get_code(':ROOT2:') is not None
    reset_roots()
    test_root1()
    assert get_code(':ROOT2:') is None

def test_onedrive_encode():
    onedrive  = onedrive_root.joinpath('OneDrive')
    assert encode_path(onedrive) == rf'{OneDriveCoder.ONEDRIVE}\OneDrive'

def test_onedrive_decode():
    dearprudence = fr'{OneDriveCoder.ONEDRIVE}\OneDrive\dear_prudence'
    assert decode_path(dearprudence) == str(onedrive_root.joinpath('OneDrive').joinpath('dear_prudence'))

def test_onedrive_add():
    onedrive  = onedrive_root.joinpath('OneDrive')
    new_code = add_root(onedrive)
    assert new_code == ':ROOT2:'
    assert get_code(new_code) == rf'{OneDriveCoder.ONEDRIVE}\OneDrive'

def test_onedrive_add2():
    onedrive = onedrive_root.joinpath('OneDrive')
    dearprudence = onedrive.joinpath('dear_prudence')
    assert encode_path(dearprudence) == fr':ROOT2:\dear_prudence'
    assert decode_path(encode_path(dearprudence)) == str(dearprudence)

def test_duplicate_root():
    NODUP = 'no duplicates please'
    root = add_root(NODUP)
    root2 = add_root(NODUP)
    assert root == root2
    assert root == add_root(NODUP)

def test_getroots_initial():
    reset_roots()
    roots = get_roots()
    assert roots == [(':ROOT1:', rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}')]

NODUP = 'no duplicates please'
def _create_test_roots():
    reset_roots()
    add_root(NODUP)
    hallo = onedrive_base.joinpath('hallo')
    add_root(hallo)       
    onedrive  = onedrive_root.joinpath('OneDrive')
    add_root(onedrive)
    
    
def test_getroots_additional():
    _create_test_roots()
    roots = get_roots()
    assert roots == [(':ROOT1:', rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}'), 
                     (':ROOT2:', NODUP), 
                     (':ROOT3:', rf':ROOT1:\hallo'),
                     (':ROOT4:', rf'{OneDriveCoder.ONEDRIVE}\OneDrive'),
                     ]
    
MOCKER = r'C:\MOCKER'
def test_mock_onedrive():
    _create_test_roots()
    set_onedrive_root(MOCKER)
    assert decode_path(':ROOT1:') == rf'{MOCKER}\{BASEPATH}'
    assert decode_path(':ROOT2:') == NODUP
    assert decode_path(':ROOT3:') == rf'{MOCKER}\{BASEPATH}\hallo'
    assert decode_path(':ROOT4:') == rf'{MOCKER}\OneDrive'

def test_expanded():
    reset_roots()
    add_root(rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}\Dinges')
    add_root(rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}\Dinges\dingetje')
    
    assert get_expanded(':ROOT2:') == decode_path(':ROOT2:')
    assert get_expanded(':ROOT3:') == decode_path(':ROOT3:')
