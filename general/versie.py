from __future__ import annotations
from dataclasses import dataclass
import datetime
from general.config import config

AAPAVERSION = '1.02'
@dataclass
class Versie:
    versie: str = '' 
    datum: str = '' 
    @staticmethod
    def datetime_str(d=datetime.datetime.now()):
        return datetime.datetime.strftime(d, '%d-%m-%Y %H:%M:%S')
def init_config():
    config.init('versie', 'versie', AAPAVERSION)
    config.init('versie', 'datum', Versie.datetime_str(datetime.datetime.now()))
init_config()

def banner():
    return f'AAPA-Afstudeer Aanvragen Proces Applicatie  versie {AAPAVERSION}'