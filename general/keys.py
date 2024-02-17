from general.singleton import Singleton
"""
    KEYS module
    ----

    classes to create unique keys

    interface functions are: 
    
    get_next_key
    and
    reset_key


"""
class Sequence:
    def __init__(self):
        self.__current = 0
    @property
    def next(self)->int:
        self.__current+=1
        return self.__current
    def reset(self, value):
        self.__current = value

class _KeysForRoot:
    def __init__(self, root:str):
        self.__root = root
        self.__sequence = Sequence()
    @property 
    def root(self):
        return self.__root
    def new_key(self)->int:
        return self.__sequence.next
    def reset(self, value):
        self.__sequence.reset(value)

class Keys(Singleton):
    def __init__(self):
        self.__generators: list[_KeysForRoot] = []
    def __add_root(self, root):
        result = _KeysForRoot(root)
        self.__generators.append(result)
        return result
    def __find_root(self, root)->_KeysForRoot:
        for generator in self.__generators:
            if generator.root==root:
                return generator
        return self.__add_root(root)       
    def new_key(self, root='key')->int:
        return self.__find_root(root).new_key()
    def reset(self, root, value=0):
        self.__find_root(root).reset(value)

_keys = Keys()
def get_next_key(root='key')->int:
    """
    Returns next key in the sequence defined by parameter root.

    parameters:
        root: str:
            the "root" of the sequence. Default is "key". 
            If more than one sequence is needed, different root identifiers can be used for each sequence

    return value:
        integer. Each call will return the previous value incremented by one.
    """
    return _keys.new_key(root)
def reset_key(root='key', value=0):
    """
    Resets key in sequence defined by parameter root.

    parameters:
        root: str
            the "root" of the sequence. Default is "key". 
        value: int
            the value to reset the sequence to. Default = 0 (meaning next call to get_next_key() will return 1).        
    """
    _keys.reset(root, value)


    