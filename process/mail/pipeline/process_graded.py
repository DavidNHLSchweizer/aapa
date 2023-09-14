from data.storage import AAPStorage
from general.log import log_info
from general.singular_or_plural import sop
from process.general.aanvraag_processor import AanvragenProcessor
from process.mail.archive_graded.archive_graded import ArchiveGradedFileProcessor
from process.mail.read_grade.read_form import ReadFormGradeProcessor
from process.mail.send_mail.create_mail import FeedbackMailProcessor

def process_graded_forms(storage: AAPStorage, filter_func = None, preview=False)->int:
    log_info('--- Verwerken ingevulde beoordelingsformulieren ...', to_console=True)
    processor = AanvragenProcessor([ReadFormGradeProcessor(),  ArchiveGradedFileProcessor(), FeedbackMailProcessor()], storage)
    result = processor.process_aanvragen(preview=preview, filter_func=filter_func) 
    log_info(f'Van {result} {sop(result, "aanvraag", "aanvragen")} de beoordeling gelezen en mail klaargezet.', to_console=True)
    log_info('--- Einde verwerken beoordelingsformulieren.', to_console=True)
    return result
