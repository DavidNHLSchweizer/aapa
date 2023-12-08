from __future__ import annotations
from pathlib import Path
import re
from typing import Tuple
from general.keys import get_next_key, reset_key
from general.log import log_info
from general.onedrive import find_onedrive_path
from general.singleton import Singleton

class RootException(Exception): pass
BASEPATH = 'NHL Stenden'

class OneDriveCoder:
    ONEDRIVE = ':ONEDRIVE:'
    def __init__(self, onedrive_root: str|Path):
        self.onedrive_root = str(Path(onedrive_root).resolve())
    def decode_onedrive(self, path: str|Path)->str:
        if not path: 
            return ''
        if isinstance(path, Path):
            path = str(path)
        if path.find(self.ONEDRIVE) == 0:
            return path.replace(self.ONEDRIVE, self.onedrive_root)
        return path
    def encode_onedrive(self, path: str|Path)->str:
        if not path: 
            return ''
        if isinstance(path, Path):
            path = str(path)
        if path.find(self.onedrive_root) == 0:
            return path.replace(self.onedrive_root, self.ONEDRIVE)
        return path
    def is_onedrive(self, path: str)->bool:
        return path.find(self.onedrive_root) == 0 

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
        self.code = code if code else self.__get_next_key(known_codes)
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
        return PathRootConvertor.__contains(path, self.code)
    def encode_path(self, path: str, allow_single=True)->str:
        return PathRootConvertor.__substitute(path, self.expanded, self.code) 
    def decode_path(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.code, self.expanded)
    def reset(self):
        reset_key(PathRootConvertor.KEYCODE, 0)

class Roots(Singleton):
    def __init__(self, base_path: str):
        self.sorter = RootSorter()
        self.reset(base_path)
    def reset(self, base_path: str):
        # self._one_drive_root = Path(find_onedrive_path(base_path)).parent
        self._onedrive_coder = OneDriveCoder(Path(find_onedrive_path(base_path)).parent)
        self._converters:list[PathRootConvertor] = []
        self._update_known()
        self.add(base_path, initial=True)
    def _update_known(self):
        self.known_codes = {converter.code for converter in self._converters}
        self.known_roots = {converter.root for converter in self._converters}       
    def decode_onedrive(self, path: str|Path)->str:        
        return self._onedrive_coder.decode_onedrive(path)
    def encode_onedrive(self, path: str|Path)->str:
        return self._onedrive_coder.encode_onedrive(path)
    def add(self, root_path: str|Path, code = None, nolog=False, initial=False)->str:
        if isinstance(root_path, Path):
            root_path = str(root_path)
        root_path = self.decode_onedrive(root_path)
        result = self._add(root_path=root_path, code=code, nolog=nolog, initial=initial)
        self._converters.sort(key=lambda converter: len(converter.expanded), reverse=True)
        return result
    def _add(self, root_path: str|Path, code = None, nolog=False, initial=False)->str:
        odp = self._find_onedrive_path(root_path, initial)
        if odp:
            encoded_path = self.encode_path(odp, allow_single=False)  
        else: 
            encoded_path = self.encode_path(root_path, allow_single=False)
        if already_there := self.__find_root(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.code
        if already_there := self.__find_code(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.code
        if self.__find_code(code):
            raise RootException(f'Duplicate code: {code}')        
        new_root = PathRootConvertor(encoded_path,
                                     odp if odp else encoded_path, 
                                     code=code, 
                                     known_codes=self.known_codes)
        if already_there := self.__find_code(new_root.root):
            log_info(f'root already there: {root_path}')
            return already_there.code
        self._converters.append(new_root)
        self._update_known()
        if not nolog:
            log_info(f'root added: {new_root.code}: "{new_root.root}"  ({new_root.expanded})')
        return new_root.code
    def _find_onedrive_path(self, path: str, initial=False)->str:
        if initial:
            return find_onedrive_path(path)
        return path if self._onedrive_coder.is_onedrive(path) else None
    def decode_path(self, path: str|Path)->str:
        if isinstance(path, Path):
            path = str(path)
        if not path:
            return ''
        path = self.decode_onedrive(path)
        for converter in self._converters:
            if converter.contains_root_code(path):
                return self.decode_path(converter.decode_path(path))
        return path
    def encode_path(self, path: str|Path, allow_single=True)->str:
        if isinstance(path, Path):
            path = str(path)
        if not path:
            return path
        path = self.decode_onedrive(path)
        candidates = set()
        for converter in self._converters:
            if converter.contains_root(path):
                candidate_encoding = converter.encode_path(path)
                candidates.add(candidate_encoding)
        for candidate in candidates:
            if len(candidate) < len(path):
                path = candidate            
        return self.encode_onedrive(path)
    def get_one_drive_root(self)->str:
        return self._onedrive_coder.onedrive_root
    def get_code(self, code: str)->str:
        if root_conv := self.__find_code(code):
            return root_conv.root
        return None
    def get_roots(self, sorted=True)->list[tuple[str,str]]:
        result = [(root_conv.code,root_conv.root) for root_conv in self._converters]
        if sorted:
            result.sort(key=lambda root_tuple: self.sorter.get_id(root_tuple[0]))
        return result
    def __find_code(self, code)->PathRootConvertor:        
        if code in self.known_codes:
            for converter in self._converters:
                if converter.code == code:
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
    return _roots.get_one_drive_root()
def decode_onedrive(path: str|Path)->str:
    return _roots.decode_onedrive(path)
def encode_onedrive(path: str|Path)->str:
    return _roots.encode_onedrive(path)

def get_code(code: str)->str:
    return _roots.get_code(code)
def get_roots(sorted=True)->list[tuple[str,str]]:
    return _roots.get_roots(sorted)

def add_root(root_path: str|Path, code: str = None, nolog=False)->str:    
    return _roots.add(root_path, code=code, nolog=nolog)
def decode_path(path: str|Path)->str:
    return _roots.decode_path(path)
def encode_path(path: str|Path, allow_single=True)->str:
    return _roots.encode_path(path, allow_single=allow_single)
def reset_roots():
    reset_key('ROOT')
    _roots.reset(BASEPATH)
