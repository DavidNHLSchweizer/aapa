from typing import Any, Tuple, Type

from data.classes.aapa_class import AAPAclass
from data.classes.detail_rec import DetailRecData
from general.classutil import find_attribute_name

main_key_name: str

class Aggregator(dict):  
    def __init__(self, owner: AAPAclass=None):
        self._classes: list[dict] = []
        self.owner = owner
    @property
    def classes(self)->list[dict]:
        return self._classes
    def class_items(self)->list[Tuple[str, Any]]:
        return [(entry['class'], entry['attribute']) for entry in self.classes]
    def class_types(self)->list[Any]:
        return [entry['class'] for entry in self.classes]
    def get_class_type(self, attribute: str)->Type[Any]:
        for entry in self.classes:
            if entry['attribute']==attribute:
                return entry['class']
        return None
    def add_class(self, class_type: Type[Any], attribute: str):
        self._classes.append({'class': class_type, 'attribute': attribute})
    def __get_hash(self, object: Any)->str:
        return f'{self.__get_class_attribute(object)}|{object.id}'
    def __get_class_attribute(self, object: Any):
        target = object if isinstance(object,type) else object.__class__
        for entry in self._classes:
            if entry['class']==target:
                return entry['attribute']
        self.__type_error(object)
    def contains(self, object: Any)->bool:
        return self.get(self.__get_hash(object), None) is not None
    def _add(self, object: Any):        
        self[self.__get_hash(object)]={'object': object, 'attribute': self.__get_class_attribute(object)}
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
    def _clear(self, class_type:str):
        for item in self.as_list(class_type).copy():
            self.remove(item)
    def clear(self, class_type:str|Any = None):
        if not class_type:
            for class_type in self.class_types():
                self._clear(class_type)
        else:
            self._clear(class_type)
    def _as_list(self, class_attribute: str)->list:
        return [value['object'] for value in self.values() if value['attribute']==class_attribute]
    def as_list(self, class_type:str|Any)->list:
        if isinstance(class_type, str):
            return self._as_list(class_type)
        return self._as_list(self.__get_class_attribute(class_type))
    def _get_ids(self, class_attribute: str):
        return [value['object'].id for value in self.values() if value['attribute']==class_attribute]
    def get_ids(self, class_type:str|Any)->list[int]:
        if isinstance(class_type, str):
            return self._get_ids(class_type)
        return self._get_ids(self.__get_class_attribute(class_type))
    # def get_detail_rec_data(self, class_type: AAPAclass)->DetailRecData:
    #     if not class_type in self.class_types():
    #         raise TypeError(f'class type: {class_type} not in this aggregator.')
    #     return DetailRecData(find_attribute_name(self.owner, self), type(self.owner),  
    #                          class_type, None)
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
    print(a.get_class_type('tweetje'))