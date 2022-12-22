import winreg
from general.keys import get_next_key
from general.log import logError
from general.singleton import Singleton

class PathRootConvertor:
    ROOTCODE = 'ROOT'
    def __init__(self, root: str):
        self.root = root
        self.root_code = f":{PathRootConvertor.ROOTCODE}{get_next_key('PathRootConvertor')}:"
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
        return PathRootConvertor.__contains(path, self.root)
    def encode_root(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.root, self.root_code)
    def contains_root_code(self, path: str)->bool:
        return PathRootConvertor.__contains(path, self.root_code)
    def decode_root(self, path: str)->str:
        return PathRootConvertor.__substitute(path, self.root_code, self.root)

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
                propertybag = f'CLSID\{subkey}\Instance\InitPropertyBag'
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, propertybag) as baggy:
                    result,_=winreg.QueryValueEx(baggy, 'TargetFolderPath')
                    return result
        return None                    
    except WindowsError as WE:
        logError(__exception_str(WE, 'WindowsError'))
        return None
    except KeyError as KE:
        logError(__exception_str(KE, 'KeyError'))
        return None
    except ValueError as VE:
        logError(__exception_str(VE, 'ValueError'))
        return None

class RootFiles(Singleton):
    def __init__(self):
        self.roots: list[PathRootConvertor] = []
    def add(self, root_path: str):
        odp = find_onedrive_path(root_path)
        self.roots.append(PathRootConvertor(odp if odp else root_path))
    def encode_root(self, path)->str:
        for root in self.roots:
            if root.contains_root(path):
                return root.encode_root(path)
        return path
    def decode_root(self, path)-> str:
        for root in self.roots:
            if root.contains_root_code(path):
                return root.decode_root(path)
        return path
        
_rootfiles = RootFiles()
def encode_path(path: str)-> str:
    return _rootfiles.encode_root(path)
def decode_path(path: str)-> str:
    return _rootfiles.decode_root(path)
def add_root(root_path: str):
    _rootfiles.add(root_path)

if __name__=='__main__':
    TESTCASES = [r'C:\repos\aapa', r'C:\Users\e3528\OneDrive - NHL Stenden\_afstuderen', r'C:\Users\e3528\NHL Stenden\HBO-ICT Afstuderen - Software Engineering']    
    TESTROOTS = ['OneDrive - NHL Stenden', 'NHL Stenden']
    for root in TESTROOTS:
        add_root(root)
    for case in TESTCASES:
        p1 = encode_path(case)
        p2 = decode_path(case)
        print(f'encoded: {p1}   decoded: {p2}')


    