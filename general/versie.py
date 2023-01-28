
from __future__ import annotations
from dataclasses import dataclass
import datetime
from general.config import config

AAPAVERSION = '0.98'
@dataclass
class Versie:
    versie: str = config.get('versie', 'versie')
    datum: str = config.get('versie', 'datum')
    @staticmethod
    def datetime_str(d=datetime.datetime.now()):
        return datetime.datetime.strftime(d, '%d-%m-%Y %H:%M:%S')
def init_config():
    config.set('versie', 'versie', AAPAVERSION)
    config.set_default('versie', 'datum', Versie.datetime_str(datetime.datetime.now()))
init_config()

