from enum import Enum, auto
import re

class Ops(Enum):
    OR  = auto()
    AND = auto()
    NOT = auto()
    IS  = auto()
    ISNOT = auto()
    EQ  = auto()
    NEQ = auto()
    GT  = auto()
    GTE = auto()
    LT  = auto()
    LTE = auto()
    HAVING = auto()
    IN   = auto()
    INNERJOIN   = auto()
    def __str__(self):
        match(self):
            case Ops.AND | Ops.OR | Ops.NOT | Ops.IS | Ops.HAVING:
                return self.name
            case Ops.ISNOT:
                return 'IS NOT'
            case Ops.EQ:
                return '='
            case Ops.NEQ:
                return '<>'
            case Ops.GT:
                return '>'
            case Ops.GTE:
                return '>='
            case Ops.LT:
                return '<'
            case Ops.LTE:
                return '<='
            case Ops.IN:
                return 'IN'
            case Ops.INNERJOIN: 
                return 'INNER JOIN'
            case _: 
                return '???'

# class SQLCFlags(Enum):
#     BRACKETS = auto(),
#     NOBRACKETS = auto(),
#     BRACKETS_OPERATOR = auto(),
#     NOBRACKETS_OPERATOR = auto(),
#     NO_COLUMN_REF = auto()

class SQLexpression:
    def __init__(self, part1, operator:Ops, part2, **flags):
        if part1 is None and not isinstance(part2, SQLexpression):
            raise SyntaxError(f'SQL expression: {part1}, {operator}, {part2}')
        self.part1 = part1
        self.operator = operator
        self.part2 = part2
        self.brackets = True
        self.apply = None
        self.column_ref_pattern = re.compile(r'.+\..+')
#TODO: uitzoeken waarom dit gedoe met column_ref niet goed werkt 
# daardoor kan je nl niet string parameters met een punt hebben, 
# dit is alleen een hack om dat weg te toveren        
        self.ignore_column_ref = False
        for flag in flags:
            match(flag.lower()):
                case 'brackets':
                    self.brackets = flags[flag]
                case 'nobrackets':
                    self.brackets = not flags[flag]
                case 'apply':
                    self.apply = flags[flag]
                case 'no_column_ref':
                    self.ignore_column_ref = flags[flag]
        self._prepare()
    def _apply(self, str):
        if self.apply:
            return f'{self.apply} ({str})'
        else:
            return str
    def _bracket(self, str):
        if self.brackets:
            return f'({str})'
        else:
            return str    
    def _bracket_apply(self, str):
        return self._bracket(self._apply(str))
    def _string(self, value):
        if isinstance(value, SQLexpression) or isinstance(value, int) or isinstance(value, float):
            return value
        elif isinstance(value, list):
            return '(' + ",".join([str(s) for s in value]) + ')'
        elif not self.brackets:
            return value
        else:
            return f'"{value}"'
    def __str__(self):
        if self.part1 == None:
            return self._bracket_apply(f'{self.operator} {self._string(self.part2)}')
        else:
            return self._bracket_apply(f'{self.part1} {self.operator} {self._string(self.part2)}')
    def _is_column_ref(self, str):        
        return self.column_ref_pattern.match(str)
    @staticmethod
    def _is_string_parameter(s: str):       
        return s and s[0] == "'" and s[-1] == "'"
    def _prepare(self):
        self._parametrized = ''
        self._parameters = []
        if isinstance(self.part1,SQLexpression):
            part1 = self.part1.parametrized
            self._parameters.extend(self.part1.parameters)
        else:
            part1 = self.part1
        if isinstance(self.part2,SQLexpression):
            part2 = self.part2.parametrized
            self._parameters.extend(self.part2.parameters)
        elif isinstance(self.part2,str) and (not self.ignore_column_ref) and self._is_column_ref(self.part2):
            part2 = self.part2
        elif isinstance(self.part2,list):
            part2 = f'({",".join(["?" for _ in self.part2])})'
            self._parameters.extend(self.part2)
        else:
            part2 = '?'
            self._parameters.append(self.part2)
        if part1 == None:
            self._parametrized = self._bracket_apply(f'{self.operator} {part2}')
        else:
            self._parametrized = self._bracket_apply(f'{part1} {self.operator} {part2}')
    @property 
    def parametrized(self)->str:
        return self._parametrized
    @property
    def parameters(self)->list[str]:
        return self._parameters
SQE=SQLexpression    

class SQEjoin(SQE):
    def __init__(self, tables: list[str], on_keys: list[str], alias: list[str] = [], **kwargs):      
        #simpele uitbreiding, niet heel uitgebreid getest. Werkt alleen voor simpele inner joins
        if len(tables) < 2:
            raise Exception('Minimaal 2 tabellen...')
        alias = SQEjoin.__get_aliases(tables, alias)
        parts = [f'{table} AS {alias}' for table,alias in zip(tables, alias)]        
        on_keys = [f"{alias}.{column}" for alias,column in zip(alias,on_keys)]
        self.on_key_expr = SQEjoin.__get_on_keys(on_keys)
        part0 = parts[0]
        part1 = parts[1]
        for index in range(2,len(parts)):
            part1 += f' INNER JOIN {parts[index]}'           
        super().__init__(part0, Ops.INNERJOIN, part1, nobrackets=True, **kwargs)
    def __str__(self)->str:
        return super().__str__() + ' ' + self.on_key_expr
    @staticmethod
    def __get_on_keys(on_keys: list[str])->str:
        result = f'ON ({SQE(on_keys[0], Ops.EQ, on_keys[1], nobrackets=True)})'
        for index in range(1,len(on_keys)-1):
            result += f' AND ({SQE(on_keys[index], Ops.EQ, on_keys[index+1], nobrackets=True)})'
        return result
    @staticmethod
    def __get_aliases(tables: list[str], alias: list[str])->list[str]:
        used = set()
        result = [SQEjoin.__create_alias(a, used) for a in alias]
        result.extend([SQEjoin.__create_alias(name[0].upper(), used) for name in tables[len(alias):]])
        return result
    @staticmethod
    def __create_alias(s: str, used: set[str])->str:
        if not s in used:
            used.add(s)
            return s
        elif len(s) == 1:
            return SQEjoin.__create_alias(f'{s}1', used)
        elif m := re.match(r'[A-Z]+(?P<n>[\d]+)', s):
            return SQEjoin.__create_alias(f'{s[0]}{int(m.group("n"))+1}', used)            
