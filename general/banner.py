from general.config import config
def banner():
    return f'AAPA-Afstudeer Aanvragen Proces Applicatie  versie {config.get("versie", "versie")}'
