from __future__ import annotations
from enum import IntEnum, auto
import json
from typing import Any, Tuple

class SQLcollType(IntEnum):
    INSERT = auto()
    UPDATE = auto()      

class SQLValuesCollector:
    def __init__(self, sql_str: str):
        self.sql_str = sql_str
        self._expected = sql_str.count('?')
        self.values:list[list[Any]] = []
    def as_dict(self)->dict[str,list[Any]]:
        return {'sql': self.sql_str, 'values': self.values}
    @classmethod
    def from_dict(cls, dump: dict)->SQLValuesCollector:
        result = cls(dump['sql'])
        for values in dump['values']:
            result.add(values)
        return result
    def add(self, values: list[Any]):
        if len(values) != self._expected:
            raise ValueError(f'not enough values in SQLValuesCollector (expected {self._expected}, got {values})')
        self.values.append(values)
    def __eq__(self, value: SQLValuesCollector)->bool:
        if self.sql_str != value.sql_str:
            return False
        if self._expected != value._expected:
            return False
        if len(self.values) != len(value.values):
            return False
        for value1, value2 in zip(self.values, value.values):
            if value1 != value2:
                return False
        return True
        
class SQLcollector:
    def __init__(self, insert_str:str, update_str: str):
        self._values = {SQLcollType.INSERT: SQLValuesCollector(insert_str), 
                        SQLcollType.UPDATE: SQLValuesCollector(update_str), 
                       }
    def collectors(self, sql_type: SQLcollType)-> SQLValuesCollector:
        return self._values[sql_type]
    def insert(self,  values: list[Any]):
        self.collectors(SQLcollType.INSERT).add(values)    
    def update(self,  values: list[Any]):
        self.collectors(SQLcollType.UPDATE).add(values)
    def sql_params(self, sql_type: SQLcollType)->Tuple[str, list[Any]]:
        collector = self.collectors(sql_type)
        for value in collector.values:
            yield (collector.sql_str, value)
    def as_dict(self)->dict:
        return {sql_type: self.collectors(sql_type).as_dict() for sql_type in SQLcollType}
    @classmethod
    def from_dict(cls, dump: dict):
        collectors = [SQLValuesCollector.from_dict(dump[key]) for key in dump.keys()]
        result = cls(collectors[0].sql_str, collectors[1].sql_str)
        result._values[SQLcollType.INSERT] = collectors[0]
        result._values[SQLcollType.UPDATE] = collectors[1]
        return result
    def dump_to_file(self, filename: str):
        with open(filename, mode='w', encoding='utf-8') as file:
            json.dump(self.as_dict(), file)
    @classmethod
    def read_from_dump(cls, filename: str)->SQLcollector:
        with open(filename, mode='r', encoding='utf-8') as file:
            return SQLcollector.from_dict(json.load(file))
    def __eq__(self, value: SQLcollector)->bool:
        return self.collectors(SQLcollType.INSERT) == value.collectors(SQLcollType.INSERT) and\
                self.collectors(SQLcollType.UPDATE) == value.collectors(SQLcollType.UPDATE)

if __name__=='__main__':      
    s = SQLcollector(insert_str='insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 
                    update_str='update STUDENTEN set stud_nr=?,full_name=?,first_name=?,email=?,status=? where id = ?')
    s.insert([71, '2012992', 'Ramön Boeie', 'Ramön', 'ramon.boeie@student.nhlstenden.com',0])
    s.update(['1678561', 'Emiel Ratelband', 'Emiel', 'emiel.ratelband@student.nhlstenden.com', 0, -1])
    s.insert([72, '2043005', 'Jasperina de Jong', 'Jasperina', 'jasperina.de.jong@student.nhlstenden.com', 0])
    s.update(['1332109', 'Wytze Waterstraal', 'Wytze', 'wytze.waterstraal@student.nhlstenden.com', 0, -1])
    s.update(['1222025', 'Donald ₡elinskini', 'Donald', 'donald.celinskini@student.nhlstenden.com', 0, -1])

    print (s.as_dict())
    s.dump_to_file('test2.json')

    print('......')

    t = SQLcollector.read_from_dump('test2.json')
    print(t.as_dict())

    if s != t:
        print('...not equal')
    else:
        print('equal!')