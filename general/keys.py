from general.singleton import Singleton

class Sequence:
    def __init__(self):
        self.__current = 0
    @property
    def next(self)->int:
        self.__current+=1
        return self.__current
    def reset(self, value):
        self.__current = value

class KeysForRoot:
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
        self.__generators: list[KeysForRoot] = []
    def __add_root(self, root):
        result = KeysForRoot(root)
        self.__generators.append(result)
        return result
    def __find_root(self, root)->KeysForRoot:
        for generator in self.__generators:
            if generator.root==root:
                return generator
        return self.__add_root(root)       
    def new_key(self, root='key')->int:
        return self.__find_root(root).new_key()
    def reset(self, root, value):
        self.__find_root(root).reset(value)

_keys = Keys()
def get_next_key(root='key')->int:
    return _keys.new_key(root)
def reset_key(root, value: int):
    print(f'resetting: {root} {value}')
    _keys.reset(root, value)


    