import winreg
from general.keys import get_next_key, reset_key
from general.log import logError, logInfo
from general.singleton import Singleton
from general.config import config

class RootException(Exception): pass

class PathRootConvertor:
    ROOTCODE = 'ROOT'
    KEYCODE  = 'PATHROOT'
    def __init__(self, root, expanded: str, code = None):
        self.root = root
        self.expanded = expanded
        self.root_code = f":{PathRootConvertor.ROOTCODE}{get_next_key(PathRootConvertor.ROOTCODE)}:" if not code else code
    @staticmethod
    def __contains(value: str, root: str)->bool:
        return len(value) >= len(root) and value[:len(root)].lower() == root.lower()
    @staticmethod
    def __substitute(value:str, substr1:str, substr2: str):
        if  PathRootConvertor.__contains(value, substr1):
            return substr2 + value[len(substr1):]
        else:
            return value
    def contains_root(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.expanded)
    def encode_root(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.expanded, self.root_code)
    def contains_root_code(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.root_code)
    def decode_root(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.root_code, self.expanded)
    def reset(self):
        reset_key(PathRootConvertor.KEYCODE, 0)

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
        print(WE)
        logError(__exception_str(WE, 'WindowsError'))
        return None
    except KeyError as KE:
        print(KE)
        logError(__exception_str(KE, 'KeyError'))
        return None
    except ValueError as VE:
        print(VE)
        logError(__exception_str(VE, 'ValueError'))
        return None

class RootFiles(Singleton):
    def __init__(self):
        self._rootconv: list[PathRootConvertor] = []
    def add(self, root_path: str, code = None):
        if already_there := self.__find_root(root_path):
            logInfo(f'root already there: {root_path}')
            return already_there.root_code
        if self.__find_code(code):
            raise RootException(f'Duplicate code: {code}')
        odp = find_onedrive_path(root_path)
        self._rootconv.append(new_root := PathRootConvertor(self.encode_root(root_path), odp if odp else self.encode_root(root_path), code=code))
        self._rootconv.sort(key=lambda r:len(r.expanded), reverse=True)
        logInfo(f'root added: {new_root.root_code}: "{new_root.root}"  ({new_root.expanded})')
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
    def __find_code(self, code)->PathRootConvertor:
        if not code:
            return None
        else:
            for r in self._rootconv:
                if r.root_code == code:
                    return r
        return None
    def __find_root(self, root_path)->PathRootConvertor:
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
    def get_roots(self)->list[tuple[str,str]]:
        result = []
        for root in self._rootconv:
            result.append((root.root_code, root.root))
        return result
        
_rootfiles = RootFiles()
def encode_path(path: str)-> str:
    return _rootfiles.encode_root(path)
def decode_path(path: str)-> str:
    return _rootfiles.decode_root(path)
def add_root(root_path: str, code: str = None)->str:
    return _rootfiles.add(root_path, code=code)
def reset_roots():
    _rootfiles.reset()
def get_roots()->list[tuple[str,str]]:
    return _rootfiles.get_roots()
def get_roots_report()->str:
    return '\n'.join([f'{code} = "{root}"' for (code,root) in get_roots()])

STANDARD_ROOTS = ['OneDrive - NHL Stenden', 'NHL Stenden']
def init_standard_roots():
    reset_roots()
    for sr in STANDARD_ROOTS:
        add_root(sr)
init_standard_roots()

def _expand_standard_root(standard_root: str)->str:
    return find_onedrive_path(standard_root)

# for r in STANDARD_ROOTS:
#     print(f'{r}: {_expand_standard_root(r)}')

if __name__=='__main__':
    TESTCASES = [r'C:\repos\aapa', r'C:\Users\e3528\OneDrive - NHL Stenden\_afstuderen', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering']    
    TESTROOTS = ['OneDrive - NHL Stenden', 'NHL Stenden', r'C:\repos']
    for root in TESTROOTS:
        add_root(root)
    for case in TESTCASES:
        p1 = encode_path(case)
        p2 = decode_path(case)
        print(f'encoded: {p1}   decoded: {p2}')


    