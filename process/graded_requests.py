from data.aanvraag_info import AanvraagBeoordeling
from general.config import config
from general.preview import Preview
from office.mail_feedback import create_feedback_mails
from office.read_beoordelingen import read_beoordelingen_from_files

def process_graded(storage, filter_func = None, preview=False):
    with Preview(preview, storage, 'graded'):
        read_beoordelingen_from_files(storage, filter_func, preview=preview)
        create_feedback_mails(storage, filter_func, preview=preview)  

