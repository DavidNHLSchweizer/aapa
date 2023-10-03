ID = 'ID'

EMPTY_ID = -1

TEXT = 'text'
INTEGER = 'integer'
REAL = 'real'
DATE = 'text' # SQLITE doesn't have a separate DATE type

NAME = 'name'
TYPE = 'type'
PRIMARY = 'primary'

REF = 'ref'
KEY = 'key'

FLAGS = 'flags'

class SyntaxError(Exception):
    pass