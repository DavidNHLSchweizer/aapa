from general.preview import Preview
from process.send_mail.mail_feedback import create_feedback_mails
from process.read_grade.read_beoordelingen import read_beoordelingen_from_files

def process_graded(storage, filter_func = None, preview=False):
    with Preview(preview, storage, 'graded'):
        read_beoordelingen_from_files(storage, filter_func, preview=preview)
        create_feedback_mails(storage, filter_func, preview=preview)  

