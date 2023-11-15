from typing import Any, Type

class Aggregator(dict):  
    def __init__(self):
        self._classes: list[dict] = []
    def add_class(self, class_type: Type[Any], alias: str):
        self._classes.append({'class': class_type, 'alias': alias})
    def __get_hash(self, object: Any)->str:
        return f'{self.__get_class_alias(object)}|{object.id}'
    def __get_class_alias(self, object: Any):
        target = object if isinstance(object,type) else object.__class__
        for entry in self._classes:
            if entry['class']==target:
                return entry['alias']
        self.__type_error(object)
    def contains(self, object: Any)->bool:
        return self.get(self.__get_hash(object), None) is not None
    def _add(self, object: Any):        
        self[self.__get_hash(object)]={'object': object, 'alias': self.__get_class_alias(object)}
    def add(self, object: Any):
        if isinstance(object, list):
            for o in object:
                self._add(o)
        else:
            self._add(object)
    def remove(self, object: Any)->Any:
        try:
            return self.pop(self.__get_hash(object))
        except KeyError as E:
            pass
    def clear(self, class_type:str|Any = None):
        if not class_type:
            super().clear()
        for item in self.as_list(class_type).copy():
            self.remove(item)
    def _as_list(self, class_alias: str)->list:
        return [value['object'] for value in self.values() if value['alias']==class_alias]
    def as_list(self, class_type:str|Any)->list:
        if isinstance(class_type, str):
            return self._as_list(class_type)
        return self._as_list(self.__get_class_alias(class_type))
    def _get_ids(self, class_alias: str):
        return [value['object'].id for value in self.values() if value['alias']==class_alias]
    def get_ids(self, class_type:str|Any)->list[int]:
        if isinstance(class_type, str):
            return self._get_ids(class_type)
        return self._get_ids(self.__get_class_alias(class_type))

    def __type_error(self, object):
        raise TypeError(f'Not supported in Aggregator: {object.__class__}')
if __name__=='__main__':
       
    class een:
        def __init__(self, id, dinges):
            self.id = id
            self.dinges = dinges
        def __str__(self):
            return f'EEN: {self.id}-{self.dinges}'
    class twee:
        def __init__(self, id, dinges):
            self.id = id
            self.dinges2 = dinges 
        def __str__(self):
            return f'TWEE: {self.id}-{self.dinges2}'

    class drie:
        def __init__(self, id, dinges):
            self.id = id
            self.dinges = dinges
        def __str__(self):
            return f'DRIE: {self.id}={self.dinges}'

    def try_add(a: Aggregator, object):
        try:
            a.add(object)
        except TypeError as TE:
            print(TE)   

    a = Aggregator()
    a.add_class(een, 'eentje')
    a.add_class(twee, 'tweetje')
    e1 = een(3, 'hello')
    e2 = een(4, 'goodbye')
    t1 = twee(6, 'doctorandus')
    t2 = twee(7, 'vijfje')
    try_add(a, [e1, e2, t1])
    try_add(a, t2)
    print('==')
    print('as list')
    for e in a.as_list(een):
        print(e)
    print('==')
    print('ids as list')
    for e in a.get_ids(een):
        print(e)
    print('==')
    print(f'removing: {t1}')
    a.remove(t1)
    for key,value in a.items():
        print(f'{str(key)}: {value}')
    a.remove(t1)
    d = drie(42, 'galactic')
    try:
        a.add(d)
    except TypeError as TE:
        print(TE)