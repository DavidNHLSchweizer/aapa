from pathlib import Path
from data.roots import BASEPATH, ONEDRIVE, add_root, decode_path, encode_path, get_code, get_onedrive_root, get_roots, reset_roots

onedrive_root = get_onedrive_root()
onedrive_base = Path(onedrive_root).joinpath(BASEPATH)

def test_root1():
    assert encode_path(onedrive_base) == ':ROOT1:'

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
    assert encode_path(onedrive) == rf'{ONEDRIVE}\OneDrive'

def test_onedrive_decode():
    dearprudence = fr'{ONEDRIVE}\OneDrive\dear_prudence'
    assert decode_path(dearprudence) == str(onedrive_root.joinpath('OneDrive').joinpath('dear_prudence'))

def test_onedrive_add():
    onedrive  = onedrive_root.joinpath('OneDrive')
    new_code = add_root(onedrive)
    assert new_code == ':ROOT2:'
    assert get_code(new_code) == rf'{ONEDRIVE}\OneDrive'

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
    assert roots == [(':ROOT1:', BASEPATH)]

def test_getroots_additional():
    NODUP = 'no duplicates please'
    add_root(NODUP)
    hallo = onedrive_base.joinpath('hallo')
    add_root(hallo)       
    onedrive  = onedrive_root.joinpath('OneDrive')
    add_root(onedrive)
    roots = get_roots()
    assert roots == [(':ROOT1:', BASEPATH), 
                     (':ROOT2:', NODUP), 
                     (':ROOT3:', rf':ROOT1:\hallo'),
                     (':ROOT4:', rf'{ONEDRIVE}\OneDrive'),
                     ]