from dataclasses import dataclass
from database.SQLbase import SQLbase
from database.viewdef import ViewDefinition

@dataclass
class ViewData:
    view_def: ViewDefinition = None
    @property
    def view_name(self)->str:
        if alias := getattr(self,'alias', None):
            return f'{self.view_def.name} as {alias}'
        else:
            return self.table_def.name
    @property
    def columns(self)->list[str]:
        return self.view_def.column_names

class SQLViewbase(SQLbase):
    def __init__(self, view_def: ViewDefinition, **args):
        self.view_data = ViewData(view_def)
        super().__init__(**args)
    @property
    def view_name(self)->str:
        return self.view_data.view_name
    @property
    def view_def(self)->ViewDefinition:
        return self.view_data.view_def
    def _getParseFlags(self):
        return []
    def _getParameters(self):
        return None        

class SQLcreateView(SQLViewbase):
    @property
    def view_name(self)->str:
        return self.view_data.view_name
    def _get_columns(self)->str:
        if self.view_def.column_names:
            return '('+ ','.join(self.view_def.column_names) + ')'
        else:
            return ''
    def _getQuery(self):
        return f'CREATE {"TEMP " if self.view_def.temp else ""}VIEW IF NOT EXISTS {self.view_name}{self._get_columns()} AS {self.view_def.select.query}'

class SQLdropView(SQLViewbase):
    def _getQuery(self):
        return f'DROP VIEW IF EXISTS {self.view_def.name};'
