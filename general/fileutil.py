""" Various filename and file-oriented utility functions. """
import datetime
import os
import sys
from pathlib import Path

MAXDEPTH=64
def writable_filename(path: str|Path)->str:
    ''' simple function to return a filename that can be opened for writing.

        not thread-safe, does not guarantee that other process will not open that file 

        parameters
        ----------
        path: the file you want to write to

        returns
        -------    
        a filename that probably can be opened for writing.
        the input path if possible. if the input path is already opened for writing, a string 
        with the form path(n) is tried, where n is incremented, starting from 1
        to prevent infinite recursion, after n has reached MAXDEPTH (64), the function returns None
        if the directory in path does not exist, the function will also return None

    '''
    if not Path(Path(path).parent).is_dir():
        return None
    if __test_can_be_written(path):
        return path        
    return __writable_filename(path, 1)
    
def __writable_filename(basepath, depth):
    if depth > MAXDEPTH:
        return None
    path = __get_filename(basepath, depth)
    if __test_can_be_written(path):
        return path
    else:
        return __writable_filename(basepath, depth+1)

def __get_filename(basepath, v):
    BP = Path(basepath)
    return BP.parent.joinpath(f'{BP.stem}({v}){BP.suffix}')

def __test_can_be_written(path):
    try:
        with open(path, "w") as _:
            return True
    except:
        return False
    
def path_with_suffix(filename: str|Path, suffix)->Path:
    """ return the filename with the given suffix (==extension). """
    if len(str(filename)) == 0: 
        return Path(filename)
    path = Path(filename)
    if path.suffix.lower() == suffix.lower():
        return path
    elif str(path.stem)[-1:] == '.':
        return path.parent.joinpath(f'{str(path.stem)[:-1]}{suffix}')
    else:
        return path.parent.joinpath(f'{path.stem}{suffix}')

def pathname_one_directory_up(path):
    return path.parent.parent.joinpath(path.stem)

def file_exists(filename: str|Path)->bool: 
    """ return True if the file exists. """
    return Path(filename).is_file()

def delete_if_exists(filename: str):
    Path(filename).unlink(missing_ok=True)

def test_file_exists(directory, filename: str)->Path: 
    """ return path to the file (in this directory) if exists (else return None). """
    p = Path(directory).joinpath(filename)
    if p.is_file():
        return p
    else:
        return None
def test_directory_exists(directory: str)->Path: 
    p = Path(directory)
    if p.is_dir():
        return p
    else:
        return None
    
def created_directory(directory: str)->bool:
    """ return True if the directory was newly created, False if it already was there."""
    if not Path(directory).is_dir():
        Path(directory).mkdir(parents=True)
        return True
    else:
        return False

def list_files(folder_name: str|Path, patterns: list[str])->list[str]:
    """ return a list of all files in the folder with the given patterns. """
    result = []
    try:
        for pattern in patterns:
            if pattern != '':
                for file in Path(folder_name).glob(pattern):
                    if file.is_file():
                        result.append(file.name)
    except:
        pass
    return result


INITIAL = 18
MAXLEN  = 64
def summary_string(s: str, initial=INITIAL, maxlen = MAXLEN):
    """ Create a shortened string for displaying very long strings.

        Replaces the "middle" part with "..."

        Intented mainly for filenames, but can be used for any string.

        parameters
        ----------
        s: the long string
        initial: the first cutoff point (everything up to initial is copied)
        maxlen: the maximum string length       
    
    """
    s = str(s)
    if maxlen == 0 or len(s) <= maxlen:
        return s
    else:
        return f'{s[0:initial]}...{s[len(s)- maxlen+initial+3:]}'

def get_main_module_path()->Path:
    """ return the path where the main module is located as determined from the commandline. """
    return Path(sys.argv[0]).resolve().parent

def from_main_path(filename: str|Path)->Path:
    """ creates filename relative to the main path. (see get_main_module_path). """
    return get_main_module_path().joinpath(filename)

def safe_file_name(filename: str, chars_to_replace=r"#%&{}\/<>:*?$!'""+`|=", replace_with= '_'):
    """ returns a "safe" filename where all illegal filename characters are replaced with "_". """
    result = filename
    if len(replace_with) == len(chars_to_replace):
        for char,replace in zip(chars_to_replace, replace_with):
            result = result.replace(char,replace)
    else:
        for char in chars_to_replace:
            result = result.replace(char,replace_with)
    return result

def last_parts_file(filename: str|Path, max_parts=3)->str:
    """ returns the last parts of a (long) filename. """
    if not filename: 
        return ''
    parts = Path(filename).parts
    parts_path = Path("...").joinpath(*parts[len(parts)-max_parts:])
    return str(parts_path)

def set_file_time(filename: str, filetime: datetime.datetime):
    """ changes the file modified time to the given date and time. """
    timestamp = filetime.timestamp()
    os.utime(filename, (timestamp,timestamp))