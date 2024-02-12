import winreg

from general.keys import get_next_key, reset_key
from main.log import log_error, log_info
from general.singleton import Singleton

class RootException(Exception): pass

class OldPathRootConvertor:
    ROOTCODE = 'ROOT'
    KEYCODE  = 'PATHROOT'
    def __init__(self, root, expanded: str, code = None, known_codes = []):
        self.root = root
        self.expanded = expanded
        self.root_code = self.__get_next_key (known_codes) if not code else code
    @staticmethod
    def __contains(value: str, root: str)->bool:
        return len(value) >= len(root) and value[:len(root)].lower() == root.lower()
    @staticmethod
    def __substitute(value:str, substr1:str, substr2: str):
        if  OldPathRootConvertor.__contains(value, substr1):
            return substr2 + value[len(substr1):]
        else:
            return value
    def __get_next_key(self, known_codes = []):
        while (key := f":{OldPathRootConvertor.ROOTCODE}{get_next_key(OldPathRootConvertor.ROOTCODE)}:") in known_codes:
            continue
        return key
    def contains_root(self, path: str)->bool:
        return OldPathRootConvertor.__contains(path, self.expanded)
    def encode_root(self, path: str)->str:
        return OldPathRootConvertor.__substitute(path, self.expanded, self.root_code)
    def contains_root_code(self, path: str)->bool:
        return OldPathRootConvertor.__contains(path, self.root_code)
    def decode_root(self, path: str)->str:
        return OldPathRootConvertor.__substitute(path, self.root_code, self.expanded)
    def reset(self):
        reset_key(OldPathRootConvertor.KEYCODE, 0)

def find_onedrive_path(resource_value: str)->str:
    def _find_value_class(namespace: str, namespace_size, resource_value: str):
        for i in range(namespace_size):
            subkey = winreg.EnumKey(namespace,i)
            with winreg.OpenKey(namespace, subkey) as sub2:
                _,nvalues,_ = winreg.QueryInfoKey(sub2)
                for j in range(nvalues): 
                    _,value,_=winreg.EnumValue(sub2,j)
                    if value == resource_value:
                        return subkey
        return None        
    def __exception_str(E, type_str):
        return f'Failure finding targetpath in Registry ({type_str}): {E}'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace") as namespace:   
            size,_,_ = winreg.QueryInfoKey(namespace)                      
            if (subkey := _find_value_class(namespace, size, resource_value)):
                propertybag = rf'CLSID\{subkey}\Instance\InitPropertyBag'
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, propertybag) as baggy:
                    result,_=winreg.QueryValueEx(baggy, 'TargetFolderPath')
                    return result
        return None                    
    except WindowsError as WE:
        log_error(__exception_str(WE, 'WindowsError'))
        return None
    except KeyError as KE:
        log_error(__exception_str(KE, 'KeyError'))
        return None
    except ValueError as VE:
        log_error(__exception_str(VE, 'ValueError'))
        return None

class OldRootFiles(Singleton):
    def __init__(self):
        self._rootconv: list[OldPathRootConvertor] = []
    def add(self, root_path: str, code = None, nolog=False):
        if already_there := self.__find_root(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.root_code
        if already_there := self.__find_code(root_path):
            log_info(f'root already there: {root_path}')
            return already_there.root_code
        if self.__find_code(code):
            raise RootException(f'Duplicate code: {code}')
        odp = find_onedrive_path(root_path)
        self._rootconv.append(new_root := OldPathRootConvertor(self.encode_root(root_path), odp if odp else self.encode_root(root_path), code=code, known_codes=self.get_known_codes()))
        self._rootconv.sort(key=lambda r:len(r.expanded), reverse=True)
        if not nolog:
            log_info(f'root added: {new_root.root_code}: "{new_root.root}"  ({new_root.expanded})')
        return new_root.root_code
    def encode_root(self, path)->str:
        if not path:
            return path
        for root in self._rootconv:
            if root.contains_root(path):
                return self.encode_root(root.encode_root(path))
        return path
    def decode_root(self, path)-> str:
        for root in self._rootconv:
            if root.contains_root_code(path):
                return self.decode_root(root.decode_root(path))
        return path
    def __find_code(self, code)->OldPathRootConvertor:
        if not code:
            return None
        else:
            for r in self._rootconv:
                if r.root_code == code:
                    return r
        return None
    def __find_root(self, root_path)->OldPathRootConvertor:
        if not root_path:
            return None
        else:
            for r in self._rootconv:
                if r.root == root_path:
                    return r
        return None
    def reset(self):
        for r in self._rootconv:
            r.reset() 
        self._rootconv = []
    def get_known_codes(self)->list[str]:
        result = []
        for root in self._rootconv:
            result.append(root.root_code)
        return result
    def get_roots(self)->list[tuple[str,str]]:
        result = []
        for root in self._rootconv:
            result.append((root.root_code, root.root))
        return result
        
_rootfiles = OldRootFiles()
def old_encode_path(path: str)-> str:
    return _rootfiles.encode_root(path)
def old_decode_path(path: str)-> str:
    return _rootfiles.decode_root(path)
def old_add_root(root_path: str, code: str = None, nolog=False)->str:    
    return _rootfiles.add(root_path, code=code, nolog=nolog)
def old_reset_roots():
    _rootfiles.reset()
def old_get_roots()->list[tuple[str,str]]:
    return _rootfiles.get_roots()
def old_get_roots_report()->str:
    return '\n'.join([f'{code} = "{root}"' for (code,root) in get_roots()])

STANDARD_ROOTS = ['OneDrive - NHL Stenden', 'NHL Stenden']
def old_init_standard_roots():
    old_reset_roots()
    for sr in STANDARD_ROOTS:
        old_add_root(sr, nolog=True) #is called before logging is properly initialized
old_init_standard_roots()
