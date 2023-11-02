from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum

from general.config import config

AAPAVERSION = '1.28'
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

class BannerPart(Enum):
    BANNER_FULL = 0
    BANNER_TITLE = 1
    BANNER_VERSION = 2

def banner(part:BannerPart = BannerPart.BANNER_FULL)->str:
    def banner_title()->str:
        return 'AAPA-Afstudeer Aanvragen Proces Applicatie'
    def banner_version()->str:
        return f'versie {AAPAVERSION}'  
    match part:
        case BannerPart.BANNER_FULL:
            return f'{banner_title()} {banner_version()}'
        case BannerPart.BANNER_TITLE:
            return banner_title()
        case BannerPart.BANNER_VERSION:
            return banner_version()
        case _: return ''
    
