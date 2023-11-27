import inspect
import re
from typing import Any, Type

def classname(o: object)->str:
    CLASSPATTERN = r"\<class '.*\.(?P<CLS>.*)'\>"
    type_str = str(o) if isinstance(o,type) else str(o.__class__)
    m = re.match(CLASSPATTERN, type_str)
    if m:
        return m.group('CLS')
    return repr(o)

def find_attribute_name(owner: Type[Any], object: Any)->str:
    # this is an imperfect hack, don't trust this to work in every situation
    # assumes that there is only one instance of this in the owner object
    if names := [name for (name,value) in inspect.getmembers(owner) if isinstance(value,type(object))]:
        if len(names) > 1:
            names = list(filter(lambda n: n[0]!= '_', names))
        return names[0]
    return ''

# def find_attribute_name_from_class(owner: Type[Any], class_type: Type[Any])->str:
#     # does not work as expected, you apparently need an actual object 
#     we get property types here, which are no indication of the actual type
#     # assumes that there is only one instance of this in the owner object
#     print(f'--------- {class_type}-------')
#     for name,value in inspect.getmembers(owner):
#         if name[0:2] == '__': continue
#         print(name,value, type(value))
#     print(f'--------- {class_type}-------')
        
    # if names := [name for (name,value) in inspect.getmembers(owner) if issubclass(value, class_type)]:
    #     if len(names) > 1:
    #         names = list(filter(lambda n: n[0]!= '_', names))
    #     return names[0]
    return ''


def find_calling_module(calling_module: str)->str:
    MODULEPATTERN = r"\<module '(?P<module>.*)' from (?P<file>.*)\>"
    def find_module_name(module_str: str)->str:
        if (m := re.match(MODULEPATTERN, module_str)):
            return m.group("module")
        return ""
    def _caller_(stack_frame: inspect.FrameInfo)->str:
        return find_module_name(str(inspect.getmodule(stack_frame[0])))       
    stack = inspect.stack()
    level = 0
    cur_module = _caller_(stack[level])
    while level < len(stack) and cur_module != calling_module:
        cur_module = _caller_(stack[level])
        level+=1
    while level < len(stack) and cur_module == calling_module:
        cur_module = _caller_(stack[level])
        level+=1
    return cur_module
