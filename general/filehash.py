from pathlib import Path
from typing import BinaryIO
from hashlib import file_digest 

def _hashfunc(file:BinaryIO):
    return file_digest(file, 'sha3_256').hexdigest()

def hash_file_digest(file: str|Path|BinaryIO)->str:
    """ return a (SHA3-256) hash in string form. """
    if isinstance(file,str|Path):
        with open(file, "rb") as file_obj:
            return _hashfunc(file_obj)
    else:
        return _hashfunc(file)
    
