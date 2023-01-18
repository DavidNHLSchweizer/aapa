from pathlib import Path

MAXDEPTH=64
def writable_filename(path):
    '''
    writable_filename: 
        simple function to return a filename that can be opened for writing
        not thread-safe, does not guarantee that other process will not open that file 

        parameters
        ----------
        path: str
            the file you want to write to

        returns
        -------    
        a filename that probably can be written to. 
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
    
def __writable_filename(basepath, n):
    if n > MAXDEPTH:
        return None
    path = __get_filename(basepath, n)
    if __test_can_be_written(path):
        return path
    else:
        return __writable_filename(basepath, n+1)

def __get_filename(basepath, n):
    BP = Path(basepath)
    return BP.parent.joinpath(f'{BP.stem}({n}){BP.suffix}')

def __test_can_be_written(path):
    try:
        with open(path, "w") as _:
            return True
    except:
        return False
def path_with_suffix(filename, suffix):
    if len(str(filename)) == 0: 
        return filename
    path = Path(filename)
    if path.suffix.lower() == suffix.lower():
        return path
    elif str(path.stem)[-1:] == '.':
        return path.parent.joinpath(f'{str(path.stem)[:-1]}{suffix}')
    else:
        return path.parent.joinpath(f'{path.stem}{suffix}')

def pathname_one_directory_up(path):
    return path.parent.parent.joinpath(path.stem)

def file_exists(filename: str)->bool: 
    return Path(filename).is_file()

def test_file_exists(directory, filename: str)->Path: 
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
    if not Path(directory).is_dir():
        Path(directory).mkdir(parents=True)
        return True
    else:
        return False

def list_files(folder_name, patterns)->list[str]:
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
