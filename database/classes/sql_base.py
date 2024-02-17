from abc import abstractmethod
from database.classes.dbargparser import dbArgParser
from database.classes.sql_expr import SQE

class SQLFlags(dbArgParser):
    COLUMNS = 1
    WHERE   = 2
    VALUES  = 3
    DISTINCT= 4
    UNIQUE  = 5
    JOINS   = 6
    ALIAS   = 7
    QUERY   = 8
    flag_map = \
        [{ "flag": COLUMNS,"attribute":'arg_columns', "default":[], "key":'column'},
         { "flag": WHERE, "attribute":'where_expression', "default":None, "key":'where'},
         { "flag": VALUES, "attribute":'values', "default":[], "key":'value'},
         { "flag": DISTINCT,"attribute":'distinct', "default": False, "key":'distinct'}, 
         { "flag": UNIQUE, "attribute":'unique', "default": False, "key":'unique'},
         { "flag": JOINS, "attribute":'joins', "default":[], "key":'join'},
         { "flag": ALIAS,"attribute":'alias', "default":'', "key":'alias'},
         { "flag": QUERY,"attribute": 'query_str', "default":"", "key": 'query'},
        ]
    def execute(self, flags, target, **args):
        self.parse(flags, target, self.flag_map, **args)
        
class SQLbase:
    def __init__(self, **args):
        SQLFlags().execute(self._get_parse_flags(), self, **args)
    def __str__(self):
        return f'{self.query}\nparams: {self.parameters}'
    @abstractmethod
    def _get_parse_flags(self):
        pass
    @abstractmethod
    def _get_query(self):
        return ''
    @abstractmethod
    def _get_parameters(self):
        return None
    @abstractmethod
    def _get_columns(self):
        return None
    @property
    def query(self):
        return self._get_query()
    @property
    def parameters(self):
        return self._get_parameters()

class SQLselectBase(SQLbase):
    def _get_parse_flags(self):
        return [SQLFlags.COLUMNS, SQLFlags.WHERE, SQLFlags.DISTINCT, SQLFlags.JOINS, SQLFlags.ALIAS, SQLFlags.QUERY]
    @abstractmethod
    def _all_columns(self)->bool:
        pass
    @abstractmethod
    def _get_name(self):
        pass
    def _get_query(self):
        if self.query_str:
            return self.query_str
        result = 'SELECT '
        if self.distinct:
            result = result + 'DISTINCT '
        if self._all_columns():
            result = result + '*'
        else:
            result = result + ','.join([column for column in self.arg_columns])
        result = result + f' FROM {self._get_name()}'
        if self.where_expression:
            result = result + '\nWHERE ' + self.where_expression.parametrized
        return result + ';'
    def _get_parameters(self):
        if not self.where_expression:
            return None
        else:
            return self.where_expression.parameters
