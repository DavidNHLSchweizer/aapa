from database.SQL import SQLFlags, SQLbase, SQLselect
from database.dbargparser import dbArgParser

class ViewFlags(dbArgParser):
    TEMP  = 1
    KEY   = 2
    ALL     = [TEMP, KEY]
    flag_map = \
        [
         { "flag": TEMP, "attribute":'temp', "default":False, "key":'temp'},
         { "key": KEY, "attribute":'key', "default":""False"", "key":'key'},
        ]
    def execute(self, target, **args):
        self.parse(ViewFlags.ALL, target, ViewFlags.flag_map, **args)

class ViewDefinition:
    def __init__(self,  name, column_names: list[str] = [], select:SQLselect = None, query='', **args):
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

class SQLcreateView(SQLbase):
    def __init__(self, view_def: ViewDefinition, **kwargs):
        self.view_def = view_def
        super().__init__(**kwargs)
    @property
    def view_name(self)->str:
        return self.view_def.name
    def _get_columns(self)->str:
        if self.view_def.column_names:
            return '('+ ','.join(self.view_def.column_names) + ')'
        else:
            return ''
    def _getQuery(self):
        return f'CREATE {"TEMP " if self.view_def.temp else ""}VIEW IF NOT EXISTS {self.view_name}{self._get_columns()} AS {self.view_def.select.Query}'
    def _getParameters(self):
        return None        
    def _getParseFlags(self):
        return []

class SQLdropView(SQLbase):
    def __init__(self, view_def: ViewDefinition, **kwargs):
        self.view_def = view_def
        super().__init__(**kwargs)
    def _getParseFlags(self):
        return []
    def _getQuery(self):
        return f'DROP VIEW IF EXISTS {self.view_def.name};'
    def _getParameters(self):
        return None
