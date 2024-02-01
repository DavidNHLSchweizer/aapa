from __future__ import annotations
from copy import deepcopy
from enum import IntEnum, auto
import json
import re
from typing import Any, Tuple

from database.database import Database

class SQLcollType(IntEnum):
    DELETE = auto()
    INSERT = auto()
    UPDATE = auto()      
    def __str__(self)->str:
        return self.name.lower()

class SQLValuesCollector:
    def __init__(self, sql_str: str, concatenate=False):
        self.sql_str = sql_str
        self._expected = sql_str.count('?')
        self.values:list[list[Any]] = []
        self.concatenate = concatenate
    def as_dict(self)->dict[str,list[Any]]:
        return {'sql': self.sql_str, 'values': self.values, 'concatenate': self.concatenate}
    @classmethod
    def from_dict(cls, dump: dict)->SQLValuesCollector:
        result = cls(dump['sql'], concatenate=dump.get('concatenate', False))
        for values in dump['values']:
            result.add(values)
        return result
    def get_sql(self)->str:
        return self.sql_str
    def get_values(self)->list[Any]:
        return [value for value in self.values]
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
        
class InsertValuesCollector(SQLValuesCollector):
    def __init__(self, sql_str: str, concatenate=True):
        super().__init__(sql_str=sql_str, concatenate=concatenate)
        PATTERN = r'.*(?P<values>\([\?\,]+\)).*'
        match = re.match(PATTERN, sql_str)
        if match:
            self._values_part = match.group('values')
    def get_sql(self)->str:
        if self.concatenate:
            full_values_part = ','.join([self._values_part] * len(self.values))
            return self.sql_str.replace(self._values_part,full_values_part)
        else:
            return super().get_sql()
    def get_values(self)->list[Any]:
        if self.concatenate:
            values = []
            for value in self.values:
                values.extend(value)
            return values
        else:
            return super().get_values()

class DeleteValuesCollector(SQLValuesCollector): 
    def __init__(self, sql_str: str, concatenate=True):
        super().__init__(sql_str=sql_str, concatenate=concatenate)
    def get_sql(self)->str:
        if self.concatenate:
            full_values_part = ','.join(['?']*len(self.values))
            return self.sql_str.replace('?',full_values_part)
        else:
            return super().get_sql()
    def get_values(self)->list[Any]:
        if self.concatenate:
            values = []
            for value in self.values:
                values.append(value[0])
            return values
        else:
            return super().get_values()

class UpdateValuesCollector(SQLValuesCollector): pass

class SQLcollector:
    TRANSLATE = {'delete': SQLcollType.DELETE, 'insert': SQLcollType.INSERT, 'update': SQLcollType.UPDATE}
    CLASSTYPE = {'delete': DeleteValuesCollector, 'insert': InsertValuesCollector, 'update': UpdateValuesCollector}
    def __init__(self, sql_data: dict[str,str]):
        self._values = {}        
        for code_str,data in sql_data.items():
            self._values[self.TRANSLATE[code_str]] = self.CLASSTYPE[code_str](data['sql'], data.get('concatenate', code_str!='update'))
    def collectors(self, sql_type: SQLcollType)->SQLValuesCollector:
        return self._values.get(sql_type, None)
    def __try_add(self, sql_type: SQLcollType, values: list[Any]):
        if (collector := self.collectors(sql_type)):
            collector.add(values)
    def delete(self,  values: list[Any]):
        self.__try_add(SQLcollType.DELETE, values)
    def insert(self,  values: list[Any]):
        self.__try_add(SQLcollType.INSERT, values)
    def update(self,  values: list[Any]):
        self.__try_add(SQLcollType.UPDATE, values)
    def sql_params(self, sql_type: SQLcollType)->Tuple[str, list[Any]]:
        collector = self.collectors(sql_type)
        for value in collector.get_values():
            yield (collector.get_sql(), value)
    def as_dict(self)->dict:
        result = {}
        for sql_type in SQLcollType:
            if (collector := self.collectors(sql_type)):
                result[str(sql_type)]=collector.as_dict()
        return result
    @classmethod
    def from_dict(cls, dump: dict):
        collectors = {key: SQLcollector.CLASSTYPE[key].from_dict(dump[key]) for key in dump.keys()}
        new_dict = {key:{'sql': collector.sql_str, 'concatenate': collector.concatenate} for key,collector in collectors.items()}
        # result = cls(dict{'delete': 'insert': collectors[0].sql_str, 'update': collectors[1].sql_str})
        result = cls(new_dict)
        for sql_coll in SQLcollType:
            result._values[sql_coll] = collectors.get(str(sql_coll))
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

class SQLcollectors(dict):
    def collectors(self, sql_type: SQLcollType)->list[SQLValuesCollector]:
        for description in self.keys():
            if not (collector := self._get(description)) or not (values_collector := collector.collectors(sql_type)): continue
            yield values_collector
    def add(self, description: str, collector: SQLcollector):
        self[description] = collector
    def _get(self, description: str)->SQLcollector:
        return self.get(description,None)
    def delete(self, description: str, values: list[Any]):
        if (collector := self._get(description)):
            collector.delete(values)
    def insert(self, description: str, values: list[Any]):
        if (collector := self._get(description)):
            collector.insert(values)
    def update(self, description: str, values: list[Any]):
        if (collector := self._get(description)):
            collector.update(values)
    def as_dict(self)->dict:
        return {description: self._get(description).as_dict() for description in self.keys()}  
    @classmethod
    def from_dict(cls, dump: dict):
        result = cls()
        for description,collector_data in dump.items():
            result.add(description, SQLcollector.from_dict(collector_data))
        return result
    def dump_to_file(self, filename: str):
        with open(filename, mode='w', encoding='utf-8') as file:
            json.dump(self.as_dict(), file)
    @classmethod
    def read_from_dump(cls, filename: str)->SQLcollectors:
        with open(filename, mode='r', encoding='utf-8') as file:
            return SQLcollectors.from_dict(json.load(file))
    def __eq__(self, value: SQLcollectors)->bool:
        if len(self.keys()) != len(value.keys()):
            return False
        for (key1,collector1),(key2,collector2) in zip(self.items(), value.items()):
            if key1 != key2 or collector1 != collector2:
                return False
        return True
    def __execute_one(self, database:Database, sql_str: str, values:list[Any], preview=False):
        if preview:
            print(f'{sql_str}\n{values}')
        else:
            database._execute_sql_command(sql_str,parameters=values)    
    def execute_sql(self, database: Database, preview = False):
        for sql_type in SQLcollType:
            for collector in self.collectors(sql_type):
                if collector is None or collector.get_values() == []:
                    continue
                sql_str = collector.get_sql()
                if collector.concatenate:
                    self.__execute_one(database, sql_str, collector.get_values(), preview)
                else:
                    for values in collector.get_values():
                        self.__execute_one(database, sql_str, values, preview)

def import_json(database: Database, json_name: str):
    sqlcolls = SQLcollectors.read_from_dump(json_name)
    sqlcolls.execute_sql(database)

if __name__=='__main__':      
    print ('--- testing single collector...')
    s = SQLcollector({
                    'insert':
                       {'sql':'insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 
                                 'concatenate': True}, 
                    'delete':
                       {'sql':'delete from STUDENTEN where id in (?)', 'concatenate': True}, 
                    'update': 
                        {'sql': 'update STUDENTEN set stud_nr=?,full_name=?,first_name=?,email=?,status=? where id = ?', 
                         'concatenate': False}})
    s.insert([71, '2012992', 'Ramön Boeie', 'Ramön', 'ramon.boeie@student.nhlstenden.com',0])
    s.delete([22])
    s.insert([72, '2043005', 'Jasperina de Jong', 'Jasperina', 'jasperina.de.jong@student.nhlstenden.com', 0])
    s.delete([23])
    s.delete([24])
    
    print (s.as_dict())
    s.dump_to_file('test2.json')

    print('......')

    t = SQLcollector.read_from_dump('test2.json')
    print(t.as_dict())

    if s != t:
        print('...not equal')
    else:
        print('equal!')

    for sql_type in SQLcollType:
        collector = s.collectors(sql_type)
        if not collector: continue
        print(f'sql: {collector.get_sql()}')
        for value in collector.get_values():
            print(f'\tvalues: {value}')

    print ('--- end testing single collector...')

    print ('--- testing multiple collectors...')

    s2 = SQLcollector({'insert': {'sql': 'insert into AANVRAGEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 
                                  'concatenate': True },
                    'update': {'sql': 'update AANVRAGEN set stud_nr=?,full_name=?,first_name=?,email=?,status=? where id = ?', 'concatenate': False}})
    s2.insert([79, '2012992', 'Ramön Boeie', 'Ramön', 'ramon.boeie@student.nhlstenden.com',0])
    s2.update(['1678561', 'Emiel Ratelband', 'Emiel', 'emiel.ratelband@student.nhlstenden.com', 0, -1])
    s2.insert([700, '2043005', 'Jasperina de Jong', 'Jasperina', 'jasperina.de.jong@student.nhlstenden.com', 0])
    s2.update(['1332109', 'Wammes Waggel', 'Wammer', 'wytze.waterstraal@student.nhlstenden.com', 0, -1])
    s2.update(['1222025', 'Donald ₡elinskini', 'Donald', 'donald.celinskini@student.nhlstenden.com', 0, -1])

    SQS = SQLcollectors()
    SQS.add('studenten', SQLcollector(
                    {'insert': {'sql': 'insert into STUDENTEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 
                                        'concatenate':True},
                    'update':  {'sql':'update STUDENTEN set stud_nr=?,full_name=?,first_name=?,email=?,status=? where id = ?',
                              'concatenate': False}}))
    SQS.add('aanvragen', SQLcollector( 
        {'insert': {'sql':'insert into AANVRAGEN (id,stud_nr,full_name,first_name,email,status) values(?,?,?,?,?,?)', 'concatenate': True},
                    'update':{'sql':'update AANVRAGEN set stud_nr=?,full_name=?,first_name=?,email=?,status=? where id = ?','concatenate': False}}))
    SQS.insert('aanvragen', [79, '2012992', 'Ramön Boeie', 'Ramön', 'ramon.boeie@student.nhlstenden.com',0])
    SQS.update('aanvragen', ['1678561', 'Emiel Ratelband', 'Emiel', 'emiel.ratelband@student.nhlstenden.com', 0, -1])
    SQS.insert('studenten', [700, '2043005', 'Jasperina de Jong', 'Jasperina', 'jasperina.de.jong@student.nhlstenden.com', 0])
    SQS.update('studenten', ['1332109', 'Wammes Waggel', 'Wammer', 'wytze.waterstraal@student.nhlstenden.com', 0, -1])
    SQS.update('studenten', ['1222025', 'Donald ₡elinskini', 'Donald', 'donald.celinskini@student.nhlstenden.com', 0, -1])
    SQS2 = deepcopy(SQS)
    print(f'checking: {SQS==SQS2}')

    SQS.dump_to_file('nova zembla.json')
    SQS3 = SQLcollectors.read_from_dump('nova zembla.json')
    print(f'checking again: {SQS3==SQS2}')

    print ('--- end testing multiple collectors...')
