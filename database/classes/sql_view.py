from dataclasses import dataclass
from database.classes.sql_base import SQLbase, SQLselectBase
from database.classes.view_def import ViewDefinition

@dataclass
class ViewData:
    view_def: ViewDefinition = None
    @property
    def view_name(self)->str:
        if alias := getattr(self,'alias', None):
            return f'{self.view_def.name} as {alias}'
        else:
            return self.view_def.name
    @property
    def columns(self)->list[str]:
        return self.view_def.column_names

class SQLselectView(SQLselectBase):
    def __init__(self, view_def: ViewDefinition, **args):
        self.view_data = ViewData(view_def)
        super().__init__(**args)    
    def _all_columns(self)->bool:
        return not self.arg_columns or self.arg_columns == []
    def _get_name(self):
        result = self.view_data.view_name
        if self.joins:
            result = result + ',' + ','.join([join for join in self.joins])
        return result

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
    def _get_parse_flags(self):
        return []
    def _get_parameters(self):
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
    def _get_query(self):
        return f'CREATE {"TEMP " if self.view_def.temp else ""}VIEW IF NOT EXISTS {self.view_name}{self._get_columns()} AS {self.view_def.select_query()};'
    
class SQLdropView(SQLViewbase):
    def _get_query(self):
        return f'DROP VIEW IF EXISTS {self.view_def.name};'
