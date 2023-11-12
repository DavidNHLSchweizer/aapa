from database.SQLbase import SQLselectBase
from database.dbargparser import dbArgParser

class ViewFlags(dbArgParser):
    TEMP  = 1
    KEY   = 2
    ALL     = [TEMP, KEY]
    flag_map = \
        [
         { "flag": TEMP, "attribute":'temp', "default":False, "key":'temp'},
         { "flag": KEY, "attribute":'key', "default":"", "key":'key'},
        ]
    def execute(self, target, **args):
        self.parse(ViewFlags.ALL, target, ViewFlags.flag_map, **args)

class ViewDefinition:
    def __init__(self,  name, column_names: list[str] = [], select:SQLselectBase = None, query='', **args):
        self.name = name
        self.column_names = column_names
        self.select = select
        self.query = query
        ViewFlags().execute(self, **args)
    def __str__(self):
        result = f'{"" if not self.temp else "TEMP "}VIEW {self.name}'
        if self.column_names:
            result = result + '\nCOLUMNS:\n\t' + ','.join(self.column_names)
        result = result + f'\n{self.query if self.query else self.select}'
        return result
    def get_keys(self)->list[str]:
        if result := getattr(self, 'key', None): 
            if isinstance(result, list):
                return result
            else:
                return [result]
        elif 'id' in self.column_names:
            return ['id']
        else:
            return [self.column_names[0]]
