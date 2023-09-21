def get_deep_attr(obj: object, attr_name: str, default: str = None):
    if (p := attr_name.find('.'))==-1:
        return getattr(obj, attr_name, default)
    else:
        return get_deep_attr(getattr(obj, attr_name[:p]), attr_name[p+1:])
    
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
