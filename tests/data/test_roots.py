from pathlib import Path
from data.general.roots import BASEPATH, OneDriveCoder, Roots

onedrive_root = Roots.get_onedrive_root()
onedrive_base = onedrive_root.joinpath(BASEPATH)

def test_root1():
    assert Roots.encode_path(onedrive_base) == ':ROOT1:'

def test_root1_code():
    expected = Path(OneDriveCoder.ONEDRIVE).joinpath(BASEPATH)
    assert Roots.get_code(':ROOT1:') == str(expected)

def test_decode_root1():
    assert Roots.decode_path(':ROOT1:') == str(onedrive_base)

def test_encode_file():
    hallo = onedrive_base.joinpath('hallo')
    assert Roots.encode_path(hallo) == rf':ROOT1:\hallo'

def test_decode_encode_file():
    hallo = onedrive_base.joinpath('hallo')
    assert Roots.decode_path(Roots.encode_path(hallo)) == str(hallo)

def test_add():
    hallo = onedrive_base.joinpath('hallo')
    new_code = Roots.add_root(hallo)
    assert new_code == ':ROOT2:'
    assert Roots.get_code(new_code) == rf':ROOT1:\hallo'
    assert Roots.encode_path(hallo) == new_code
    assert Roots.encode_path(hallo.joinpath('goodbye')) == rf':ROOT2:\goodbye'

def test_reset():
    test_root1()
    assert Roots.get_code(':ROOT2:') is not None
    Roots.reset_roots()
    test_root1()
    assert Roots.get_code(':ROOT2:') is None

def test_onedrive_encode():
    onedrive  = onedrive_root.joinpath('OneDrive')
    assert Roots.encode_path(onedrive) == rf'{OneDriveCoder.ONEDRIVE}\OneDrive'

def test_onedrive_decode():
    dearprudence = fr'{OneDriveCoder.ONEDRIVE}\OneDrive\dear_prudence'
    assert Roots.decode_path(dearprudence) == str(onedrive_root.joinpath('OneDrive').joinpath('dear_prudence'))

def test_onedrive_add():
    onedrive  = onedrive_root.joinpath('OneDrive')
    new_code = Roots.add_root(onedrive)
    assert new_code == ':ROOT2:'
    assert Roots.get_code(new_code) == rf'{OneDriveCoder.ONEDRIVE}\OneDrive'

def test_onedrive_add2():
    onedrive = onedrive_root.joinpath('OneDrive')
    dearprudence = onedrive.joinpath('dear_prudence')
    assert Roots.encode_path(dearprudence) == fr':ROOT2:\dear_prudence'
    assert Roots.decode_path(Roots.encode_path(dearprudence)) == str(dearprudence)

def test_duplicate_root():
    NODUP = 'no duplicates please'
    root = Roots.add_root(NODUP)
    root2 = Roots.add_root(NODUP)
    assert root == root2
    assert root == Roots.add_root(NODUP)

def test_getroots_initial():
    Roots.reset_roots()
    roots = Roots.get_roots()
    assert roots == [(':ROOT1:', rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}')]

NODUP = 'no duplicates please'
def _create_test_roots():
    Roots.reset_roots()
    Roots.add_root(NODUP)
    hallo = onedrive_base.joinpath('hallo')
    Roots.add_root(hallo)       
    onedrive  = onedrive_root.joinpath('OneDrive')
    Roots.add_root(onedrive)
    
    
def test_getroots_additional():
    _create_test_roots()
    roots = Roots.get_roots()
    assert roots == [(':ROOT1:', rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}'), 
                     (':ROOT2:', NODUP), 
                     (':ROOT3:', rf':ROOT1:\hallo'),
                     (':ROOT4:', rf'{OneDriveCoder.ONEDRIVE}\OneDrive'),
                     ]
    
MOCKER = r'C:\MOCKER'
def test_mock_onedrive():
    _create_test_roots()
    Roots.set_onedrive_root(MOCKER)
    assert Roots.decode_path(':ROOT1:') == rf'{MOCKER}\{BASEPATH}'
    assert Roots.decode_path(':ROOT2:') == NODUP
    assert Roots.decode_path(':ROOT3:') == rf'{MOCKER}\{BASEPATH}\hallo'
    assert Roots.decode_path(':ROOT4:') == rf'{MOCKER}\OneDrive'

def test_expanded():
    Roots.reset_roots()
    Roots.add_root(rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}\Dinges')
    Roots.add_root(rf'{OneDriveCoder.ONEDRIVE}\{BASEPATH}\Dinges\dingetje')
    
    assert Roots.get_expanded(':ROOT2:') == Roots.decode_path(':ROOT2:')
    assert Roots.get_expanded(':ROOT3:') == Roots.decode_path(':ROOT3:')
