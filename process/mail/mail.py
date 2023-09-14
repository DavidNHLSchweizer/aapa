from general.preview import Preview
from process.mail.pipeline.process_graded import process_graded_forms
from process.mail.send_mail.create_mail import create_feedback_mails
from process.mail.read_grade.read_beoordelingen import read_beoordelingen_from_files

def process_graded(storage, filter_func = None, preview=False):
    with Preview(preview, storage, 'graded'):
        process_graded_forms(storage, filter_func, preview=preview)
        # read_beoordelingen_from_files(storage, filter_func, preview=preview)
        # create_feedback_mails(storage, filter_func, preview=preview)  

