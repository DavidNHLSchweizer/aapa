from dataclasses import dataclass
from database.dbConst import EMPTY_ID

@dataclass
class BaseDir:
    year: int
    period: str
    forms_version: str
    directory: str
    id: int = EMPTY_ID

