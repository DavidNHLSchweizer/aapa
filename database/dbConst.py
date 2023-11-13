from typing import Type

ID = 'ID'
EMPTY_ID = -1

TEXT = 'TEXT'
INTEGER = 'INTEGER'
REAL = 'REAL'
DATE = 'TEXT' # SQLITE doesn't have a separate DATE type


NAME = 'name'
TYPE = 'type'
PRIMARY = 'primary'

REF = 'ref'
KEY = 'key'

FLAGS = 'flags'

class SyntaxError(Exception):
    pass