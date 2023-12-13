from database.dbargparser import dbArgParser
from database.sql_expr import SQEjoin

class ViewFlags(dbArgParser):
    TEMP    = 1
    KEY     = 2
    COLUMNS = 3
    WHERE   = 4
    ALL     = [TEMP, KEY, COLUMNS, WHERE]
    flag_map = \
        [
         { "flag": TEMP, "attribute":'temp', "default":False, "key":'temp'},
         { "flag": KEY, "attribute":'_key', "default":"", "key":'key'},
         { "flag": COLUMNS,"attribute": '_columns', "default":None, "key":'columns'},
         { "flag": WHERE,"attribute": 'where', "default":None, "key":'where'},
        ]
    def execute(self, target, **args):
        self.parse(ViewFlags.ALL, target, ViewFlags.flag_map, **args)

class ViewDefinition:
    def __init__(self,  name, column_names: list[str] = [], join_expression:SQEjoin = None, query='', **args):
        self.name = name
        self.column_names = column_names
        self.join_expression = join_expression
        self.query = query
        self.parameters = []
        ViewFlags().execute(self, **args)
        if self.where:
            self.parameters.extend(self.where.parameters)
    def __str__(self):
        result = f'{"" if not self.temp else "TEMP "}VIEW {self.name}'
        if self.column_names:
            result = result + '\nCOLUMNS:\n\t' + ','.join(self.column_names)
        result = result + f'\n{self.query if self.query else self.join_expression}'
        if self.where:
            result += f' WHERE {self.where}'
        return result
    def select_query(self)->str:
        if self.query:
            return self.query
        else:
            if self._columns:
                columns = ','.join(self._columns)
            else:
                columns = ','.join(self.column_names)
            result =  f"SELECT {columns} FROM {self.join_expression}"        
            if self.where:
                result += f' WHERE {self.where}'
            return result
    def get_keys(self)->list[str]:
        if result := getattr(self, '_key', None): 
            if isinstance(result, list):
                return result
            else:
                return [result]
        elif 'id' in self.column_names:
            return ['id']
        else:
            return [self.column_names[0]]
    @property
    def key(self)->str:
        return self.get_keys()[0]


