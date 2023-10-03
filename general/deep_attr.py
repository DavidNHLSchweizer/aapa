def _dot_pos(attr_name: str)->bool:
    return attr_name.find('.') 

def has_deep_attr(attr_name: str)->bool:
    return _dot_pos(attr_name) >= 0

def get_deep_attr(obj: object, attr_name: str, default: str = None):
    if has_deep_attr(attr_name):
        p = _dot_pos(attr_name)
        return get_deep_attr(getattr(obj, attr_name[:p]), attr_name[p+1:])
    else:
        return getattr(obj, attr_name, default)

def deep_attr_main_part(attr_name: str)->str:
    if (p := _dot_pos(attr_name)) >= 0:
        return attr_name[:p]
    else:
        return attr_name

def deep_attr_sub_part(attr_name: str)->str:
    if (p := _dot_pos(attr_name)) >= 0:
        return attr_name[p+1:]
    else:
        return attr_name

if __name__ == '__main__':    
    class test:
        def __init__(self, value):
            self.value= value
    class pest:
        def __init__(self, value2):
            self.value2 = value2
            self.t = test(value2 * 2)         
    class dubbel:
        def __init__(self):
            self.ppp = pest(33)        
    p = pest(42)
    print (get_deep_attr(p, 'value2'))
    print (get_deep_attr(p, 't.value'))

    d = dubbel()
    print(get_deep_attr(d, 'ppp.t.value'))
