from pathlib import Path
import re
from typing import Tuple
from general.keys import get_next_key, reset_key
from general.log import log_info
from general.onedrive import find_onedrive_path
from general.singleton import Singleton

class RootException(Exception): pass
ONEDRIVE = ':ONEDRIVE:'
BASEPATH = 'NHL Stenden'

class RootSorter:
    PATTERN=r':ROOT(?P<N>\d*):'
    def __init__(self):
        self.pattern = re.compile(self.PATTERN)
    def get_id(self, code: str)->int:
        if m := self.pattern.match(code):
            return int(m.group('N'))
        return -1
    def sorted_roots(self, roots: list[Tuple[str,str]])->list[Tuple[str,str]]:
        return sorted(roots, key=lambda x: self.get_id(x[0]))  
    
class PathRootConvertor:
    ROOTCODE = 'ROOT'
    KEYCODE  = 'PATHROOT'
    def __init__(self, root, expanded: str, code = None, known_codes:set[str] = set()):
        self.root = root
        self.expanded = expanded
        self.root_code = self.__get_next_key(known_codes) if not code else code
    @staticmethod
    def __contains(value: str, root: str)->bool:
        return len(value) >= len(root) and value[:len(root)].lower() == root.lower()
    @staticmethod
    def __substitute(value:str, substr1:str, substr2: str):
        if  PathRootConvertor.__contains(value, substr1):
            return substr2 + value[len(substr1):]
        else:
            return value
    def __get_next_key(self, known_codes:set[str] = set()):
        while (key := f":{PathRootConvertor.ROOTCODE}{get_next_key(PathRootConvertor.ROOTCODE)}:") in known_codes:
            continue
        return key
    def contains_root(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.expanded)
    def contains_root_code(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.root_code)
    def encode_path(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.expanded, self.root_code)
    def decode_path(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.root_code, self.expanded)
    def reset(self):
        reset_key(PathRootConvertor.KEYCODE, 0)

class Roots(Singleton):
    def __init__(self, base_path: str):
        self.sorter = RootSorter()
        self.reset(base_path)
    def reset(self, base_path: str):
        self._one_drive_root = Path(find_onedrive_path(base_path)).parent
        self._converters:list[PathRootConvertor] = []
        self._update_known()
        self.add(base_path, initial=True)
    def _update_known(self):
        self.known_codes = {converter.root_code for converter in self._converters}
        self.known_roots = {converter.root for converter in self._converters}       
    def add(self, root_path: str|Path, code = None, nolog=False, initial=False)->str:
        if isinstance(root_path, Path):
            root_path = str(root_path)
        result = self._add(root_path=root_path, code=code, nolog=nolog, initial=initial)
        self._converters.sort(key=lambda root_conv: self.sorter.get_id(root_conv.root_code), reverse=True)
        return result
    def _add(self, root_path: str|Path, code = None, nolog=False, initial=False)->str:
        if already_there := self.__find_root(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.root_code
        if already_there := self.__find_code(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.root_code
        if self.__find_code(code):
            raise RootException(f'Duplicate code: {code}')        
        odp = self._find_onedrive_path(root_path, initial)
        new_root = PathRootConvertor(self.encode_path(root_path), 
                                     odp if odp else self.encode_path(root_path), 
                                     code=code, 
                                     known_codes=self.known_codes)
        if already_there := self.__find_code(new_root.root):
            log_info(f'root already there: {root_path}')
            return already_there.root_code
        self._converters.append(new_root)
        self._update_known()
        if not nolog:
            log_info(f'root added: {new_root.root_code}: "{new_root.root}"  ({new_root.expanded})')
        return new_root.root_code
    def _find_onedrive_path(self, path: str, initial=False)->str:
        if initial:
            return find_onedrive_path(path)
        if path.find(str(self._one_drive_root))==0:
            return path
        return None
    def decode_path(self, path: str|Path)->str:
        if isinstance(path, Path):
            path = str(path)
        if not path:
            return ''
        if path.find(ONEDRIVE) == 0:
            path = path.replace(ONEDRIVE, str(self._one_drive_root))
        for converter in self._converters:
            if converter.contains_root_code(path):
                return self.decode_path(converter.decode_path(path))
        return path
    def encode_path(self, path: str|Path)->str:
        if isinstance(path, Path):
            path = str(path)
        if not path:
            return path
        candidates = set()
        for converter in self._converters:
            if converter.contains_root(path):
                candidate_encoding = self.encode_path(converter.encode_path(path))
                candidates.add(candidate_encoding)
        for candidate in candidates:
            if len(candidate) < len(path):
                path = candidate            
        if path.lower().find(str(self._one_drive_root).lower()) == 0:
            return rf'{ONEDRIVE}{path[len(str(self._one_drive_root)):]}'
        return path
    def get_code(self, code: str)->str:
        if root_conv := self.__find_code(code):
            return root_conv.root
        return None
    def get_roots(self, sorted=True)->list[tuple[str,str]]:
        result = [(root_conv.root_code,root_conv.root) for root_conv in self._converters]
        if sorted:
            result.sort(key=lambda root_tuple: self.sorter.get_id(root_tuple[0]))
        return result
    def __find_code(self, code)->PathRootConvertor:        
        if code in self.known_codes:
            for converter in self._converters:
                if converter.root_code == code:
                    return converter
        return None
    def __find_root(self, root_path)->PathRootConvertor:
        if not root_path:
            return None
        else:
            for converter in self._converters:
                if converter.root == root_path:
                    return converter
        return None

_roots = Roots(BASEPATH)

def get_onedrive_root()->Path:
    return _roots._one_drive_root
def get_code(code: str)->str:
    return _roots.get_code(code)
def get_roots(sorted=True)->list[tuple[str,str]]:
    return _roots.get_roots(sorted)

def add_root(root_path: str|Path, code: str = None, nolog=False)->str:    
    return _roots.add(root_path, code=code, nolog=nolog)
def decode_path(path: str|Path)->str:
    return _roots.decode_path(path)
def encode_path(path: str|Path)->str:
    return _roots.encode_path(path)
def reset_roots():
    reset_key('ROOT')
    _roots.reset(BASEPATH)
