
from __future__ import annotations
from dataclasses import dataclass
import datetime
from time import strftime
from general.config import config

@dataclass
class Versie:
    db_versie: str = config.get('versie', 'db_versie')
    versie: str = config.get('versie', 'versie')
    datum: str = config.get('versie', 'datum')
    @staticmethod
    def datetime_str(d):
        return datetime.datetime.strftime(d, '%d-%m-%Y %H:%M:%S')


