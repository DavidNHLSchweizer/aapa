import winreg
from general.log import log_error

def find_onedrive_path(resource_value: str)->str:
    NAMESPACE=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace"
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
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, NAMESPACE) as namespace:   
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

