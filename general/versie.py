from __future__ import annotations

import datetime
from dataclasses import dataclass

from general.config import config

AAPAVERSION = '1.21'
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
    if config.get('versie', 'versie') != AAPAVERSION:
        config.set('versie', 'versie', AAPAVERSION)
init_config()

BANNER_FULL = 0
BANNER_TITLE = 1
BANNER_VERSION = 2

def banner(part:int = BANNER_FULL)->str:
    def banner_title()->str:
        return 'AAPA-Afstudeer Aanvragen Proces Applicatie'
    def banner_version()->str:
        return f'versie {AAPAVERSION}'
    
    if part == BANNER_FULL:
        return f'{banner_title()} {banner_version()}'
    elif part == BANNER_TITLE:
        return banner_title()
    elif part == BANNER_VERSION:
        return banner_version()
    return None
    
