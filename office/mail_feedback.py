from pathlib import Path
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import created_directory, path_with_suffix
from office.beoordeling_formulieren import MailMergeException
from office.mail_merge import MailMerger
from data.storage import AAPStorage
from office.mail_sender import FeedbackMailCreator, OutlookMail, OutlookMailDef
from office.word_processor import WordDocument, WordReaderException
from general.log import logError, logInfo, logPrint

class FeedbackMailsCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_docs:dict, default_maildef: OutlookMailDef, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.mailer = FeedbackMailCreator()
        # self.merger = FeedbackMailMerger(storage, template_docs, default_maildef, output_directory)
    def get_draft_folder_name(self):
        return self.mailer.draft_folder_name
    def _process_aanvragen(self, aanvragen: list[AanvraagInfo], preview=False)->int:
        result = 0        
        for aanvraag in aanvragen:
            if aanvraag.status != AanvraagStatus.GRADED:
                continue            
            filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
            if preview:
                print(f'\tKlaarzetten mail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.email} met als attachment: {filename}')
            else:
                self.mailer.draft_mail(aanvraag, filename)
                logPrint(f'Feedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.student_name} ({aanvraag.student.email}) klaargezet in {self.draft_folder_name}.')
            result += 1        
        return result
    def process(self, filter_func = None, preview=False)->int:
        return self._process_aanvragen(self.filtered_aanvragen(filter_func), preview=preview)

def create_feedback_mails(storage: AAPStorage, templates: dict, default_maildef: OutlookMailDef, output_directory, filter_func = None, preview=False):
    logPrint('--- Klaarzetten feedback mails...')
    if preview:
        if not Path(output_directory).is_dir():
            print(f'Map {output_directory} aan te maken.')
    else:
        if created_directory(output_directory):
            logPrint(f'Map {output_directory} aangemaakt.')
    storage.add_file_root(str(output_directory))
    file_creator = FeedbackMailsCreator(storage, templates, default_maildef, output_directory)
    n_mails = file_creator.process(filter_func, preview=preview)
    klaargezet = 'klaar te zetten' if preview else 'klaargezet'    
    logPrint(f'### {n_mails} mails {klaargezet} in Outlook {file_creator.get_draft_folder_name()}')
    logPrint('--- Einde klaarzetten feedback mails.')
