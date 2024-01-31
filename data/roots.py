from __future__ import annotations
from pathlib import Path
import re
import ctypes
import locale
from typing import Tuple
from general.keys import get_next_key, reset_key
from general.log import log_debug, log_info
from general.onedrive import find_onedrive_path
from general.singleton import Singleton


class RootException(Exception): pass
BASEPATH = r'NHL Stenden'

class OneDriveCoder:
    ONEDRIVE = ':ONEDRIVE:'
    DOCUMENTS = ':DOCUMENTS:'
    onedrive_root = None
    def __init__(self, onedrive_root: str|Path):
        OneDriveCoder.onedrive_root =Path(onedrive_root).resolve() 
        self._documents = self._init_get_documents_translation()
    def _init_get_documents_translation(self):        
        # hack to find whether it is xxxx - Documents or xxxx - Documenten
        # locale for computer does not work for this, the onedrive language is 
        # apparently not dependent on the local computer language
        # so just test the two possibilities to find which one works
        _SHARED_DOCUMENTS_PATH = rf'{self.ONEDRIVE}\{BASEPATH}\HBO-ICT Afstuderen - :DOCUMENTS:'
        # this is the only path we are interested in
        for translation in ['Documents', 'Documenten']:
            d =  _SHARED_DOCUMENTS_PATH.replace(self.ONEDRIVE, str(self.onedrive_root)).replace(self.DOCUMENTS, translation)
            if Path(d).is_dir():
                return translation
        return 'Documents'
    def decode_onedrive(self, path: str|Path, onedrive_root=None)->str:
        if not path: 
            return ''
        if isinstance(path, Path):
            path = str(path)
        if path.find(self.ONEDRIVE) == 0:
            result = path.replace(self.ONEDRIVE, str(onedrive_root if onedrive_root else self.onedrive_root))
            return result.replace(self.DOCUMENTS, self._documents)
        return path
    def encode_onedrive(self, path: str|Path)->str:
        if not path: 
            return ''
        if isinstance(path, Path):
            path = str(path)
        if self.onedrive_root and path.lower().find(str(self.onedrive_root).lower()) == 0:
            result = self.ONEDRIVE+path[len(str(self.onedrive_root)):]
            return result.replace(self._documents, self.DOCUMENTS)
        return path
    def is_onedrive(self, path: str)->bool:
        return path.find(str(self.onedrive_root)) == 0 

class RootSorter:
    PATTERN=r'^:ROOT(?P<N>\d*):$'
    def __init__(self):
        self.pattern = re.compile(self.PATTERN)
    def get_id(self, code: str)->int:
        if m := self.pattern.match(code):
            return int(m.group('N'))
        return -1
    def sorted_roots(self, roots: list[Tuple[str,str]])->list[Tuple[str,str]]:
        return sorted(roots, key=lambda x: self.get_id(x[0]))  
    def is_single_root(self, path: str)->bool:
        return self.pattern.match(path) is not None

class PathRootConvertor:
    ROOTCODE = 'ROOT'
    KEYCODE  = 'PATHROOT'
    def __init__(self, root, expanded: str, code = None, known_codes:set[str] = set()):
        self.root = root
        self.expanded = expanded
        self.code = code if code else self.__get_next_key(known_codes)
    def __str__(self)->str:
        return f'code=[{self.code}] root=[{self.root}] expanded=[{self.expanded}]'
    @staticmethod
    def __contains(value: str, root: str)->bool:
        return value.lower()==root.lower() or (len(value) >= len(root) and len(Path(value[len(root):]).parts) > 1 and value[:len(root)].lower() == root.lower())
    @staticmethod
    def __substitute(value:str, substr1:str, substr2: str)->str:
        if  PathRootConvertor.__contains(value, substr1):
            return substr2 + value[len(substr1):]
        else:
            return value
    def __get_next_key(self, known_codes:set[str] = set())->str:
        while (key := f":{PathRootConvertor.ROOTCODE}{get_next_key(PathRootConvertor.ROOTCODE)}:") in known_codes:
            continue
        return key
    def contains_root(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.expanded) 
    def contains_root_code(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.code)
    def encode_path(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.expanded, self.code) 
    def decode_path(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.code, self.expanded)
    def reset(self):
        reset_key(PathRootConvertor.KEYCODE, 0)
    def replace_onedrive(self, old_onedrive: Path, new_onedrive: Path):       
        if PathRootConvertor.__contains(self.expanded, str(old_onedrive)):
            self.expanded = PathRootConvertor.__substitute(self.expanded, str(old_onedrive), str(new_onedrive))

class Roots(Singleton):
    def __init__(self, base_path: str):
        self._sorter = RootSorter()
        self._initialized = False
        self.reset(base_path)
    def reset(self, base_path: str):
        self._converters:list[PathRootConvertor] = []
        self._update_known()
        if not self._initialized:
            path = find_onedrive_path(base_path)
            self._onedrive_coder = OneDriveCoder(Path(path).parent)
            self._initialized = True       
        else:
            path=Path(self.get_one_drive_root()).joinpath(base_path)
        self.add(self.encode_onedrive(path))
    def _update_known(self):
        self.known_codes = {converter.code for converter in self._converters}
        self.known_roots = {converter.root for converter in self._converters}       
    def decode_onedrive(self, path: str|Path, onedrive_root=None)->str:        
        return self._onedrive_coder.decode_onedrive(path, onedrive_root=onedrive_root)
    def encode_onedrive(self, path: str|Path)->str:
        return self._onedrive_coder.encode_onedrive(path)
    def add(self, root_path: str|Path, code = None)->str:  
        if isinstance(root_path, Path):
            root_path = str(root_path)
        root_path = self.decode_onedrive(root_path)
        result = self._add(root_path=root_path, code=code)
        self._sort()
        return result
    def _sort(self):
        self._converters.sort(key=lambda converter: len(converter.expanded), reverse=True)
    def _add(self, root_path: str|Path, code = None)->str:
        if already_there := self.__find_expanded(root_path):
            log_debug(f'expanded path root already there: {root_path}')
            return already_there.code
        odp = self._find_onedrive_path(root_path)
        if odp:
            encoded_path = self.encode_path(odp, allow_single=False)  
        else: 
            encoded_path = self.encode_path(root_path, allow_single=False)
        if already_there := self.__find_root(root_path):
            log_debug(f'root already there: {root_path}')
            return already_there.code
        if already_there := self.__find_code(root_path):
            log_debug(f'root already there: {root_path}')
            return already_there.code
        if self.__find_code(code):
            raise RootException(f'Duplicate code: {code}')        
        new_root = PathRootConvertor(encoded_path,
                                     odp if odp else encoded_path, 
                                     code=code, 
                                     known_codes=self.known_codes)
        if already_there := self.__find_code(new_root.root):
            log_debug(f'root already there: {root_path}')
            return already_there.code
        self._converters.append(new_root)
        self._update_known()
        log_debug(f'root added: {new_root.code}: "{new_root.root}"  ({new_root.expanded})')
        return new_root.code
    def _find_onedrive_path(self, path: str)->str:
        if not self._initialized:
            self._initialized = True
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
                if allow_single or not self._sorter.is_single_root(candidate_encoding):
                    candidates.add(candidate_encoding)
        if len(candidates) == 1:
            encoded = list(candidates)[0] # to also cover extreme cases (very short paths, shorted than the coded path)
        else:
            encoded = path
            for candidate in candidates:
                if len(candidate) < len(encoded):
                    encoded = candidate
        return self.encode_onedrive(encoded)
    def get_one_drive_root(self)->Path:
        return self._onedrive_coder.onedrive_root
    def replace_onedrive(self, old_onedrive: str, new_onedrive: str):
        for converter in self._converters:
            converter.replace_onedrive(str(old_onedrive), str(new_onedrive))
        self._sort()        
    def set_onedrive_root(self, path: str):
        old_root = self._onedrive_coder.onedrive_root
        self._onedrive_coder.onedrive_root = path
        self.replace_onedrive(old_root, path)
    def get_code(self, code: str)->str:
        if root_conv := self.__find_code(code):
            return root_conv.root
        return None
    def get_expanded(self, code: str)->str:
        if root_conv := self.__find_code(code):
            return root_conv.expanded
        return None
    def get_roots(self, sorted=True)->list[tuple[str,str]]:
        result = [(root_conv.code,root_conv.root) for root_conv in self._converters]
        if sorted:
            result.sort(key=lambda root_tuple: self._sorter.get_id(root_tuple[0]))
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
    def __find_expanded(self, root_path)->PathRootConvertor:
        if not root_path:
            return None
        else:
            for converter in self._converters:
                if converter.expanded == root_path:
                    return converter
        return None
    def dump(self, filename: str, msg='', append = False):
        with open(filename, mode = "a" if append else "w", encoding='utf-8') as file:
            if msg: 
                file.write(f'{msg}\n')
            for n,converter in enumerate(self._converters):
                file.write(f'{n}:{str(converter)}\n')


_roots = Roots(BASEPATH)

def set_onedrive_root(path: str):
    _roots.set_onedrive_root(path)
def get_onedrive_root()->Path:
    return _roots.get_one_drive_root()
def decode_onedrive(path: str|Path, onedrive_root=None)->str:
    return _roots.decode_onedrive(path, onedrive_root=onedrive_root)
def encode_onedrive(path: str|Path)->str:
    return _roots.encode_onedrive(path)

def get_code(code: str)->str:
    return _roots.get_code(code)
def get_expanded(code: str)->str:
    return _roots.get_expanded(code)
def get_roots(sorted=True)->list[tuple[str,str]]:
    return _roots.get_roots(sorted)

def add_root(root_path: str|Path, code: str = None)->str:    
    """ add a new root to the list used for encodepath/decodepath.

        parameters:
            root_path: str or pathlib.Path
                the new root path to encode.
            code: str = None
                the code to use for this root_path.
                if code is None (or not given), the code value is generated.
        returns:
            the new root code.
    """
    return _roots.add(root_path, code=code)
def decode_path(path: str|Path)->str:
    """decode an encoded path (encoded with encode_path)."""
    return _roots.decode_path(path)
def encode_path(path: str|Path, allow_single=True)->str:
    r""" encode a path (for storing in the database).
            replaces appropiate parts with :ROOTnn: codes as defined earlier with add_root.
        parameters:
            path: str or pathlib.Path   the path to encode
            allow_single=True: if False, a encoded path of just :ROOTnn: is not allowed.
        returns: 
            the "best possible" encoded path. 
            "best possible" means: (in order of priority)
            1) a single root code (:ROOTnn:), e.g. :ROOT42:)
            2) the shortest string found of the form :ROOTnn:\[end_of_path]
                e.g. :ROOT42:\padje\file.doc
            3) the full pathname (if the filename is not mapped to one of the known roots).
            The encoded path will not have more than one root code (root codes can be nested, however).           
    """
    return _roots.encode_path(path, allow_single=allow_single)
def reset_roots():
    reset_key('ROOT')
    _roots.reset(BASEPATH)

def dump_roots(filename: str, msg = '', append = False):
    _roots.dump(filename, msg, append)