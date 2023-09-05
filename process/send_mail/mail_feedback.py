from pathlib import Path
from data.classes import AanvraagInfo
from general.config import ListValueConvertor, config
from general.fileutil import from_main_path, summary_string
from process.aanvraag_processor import AanvraagProcessor
from data.classes import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileType
from data.storage import AAPStorage
from general.substitutions import FieldSubstitution, FieldSubstitutions
from process.aanvraag_state_processor import NewAanvraagProcessor, NewAanvragenProcessor
from process.send_mail.mail_sender import OutlookMail, OutlookMailDef
from general.log import logError, logPrint


def init_config():
    config.register('mail', 'feedback_mail_templates', ListValueConvertor)
    config.init('mail', 'feedback_mail_templates', [r'.\templates\template_afgekeurd.htm', r'.\templates\template_goedgekeurd.htm'])
    config.init('mail', 'subject', 'Beoordeling aanvraag afstuderen ":TITEL:"')
    config.register('mail', 'cc', ListValueConvertor)
    config.init('mail', 'cc', ['afstuderenschoolofict@nhlstenden.com'])
    config.register('mail', 'bcc', ListValueConvertor)
    config.init('mail', 'bcc', ['david.schweizer@nhlstenden.com', 'bas.van.hensbergen@nhlstenden.com', 'joris.lops@nhlstenden.com'])
    config.init('mail', 'onbehalfof', 'afstuderenschoolofict@nhlstenden.com')
init_config()

def get_feedback_mail_templates():
    return [from_main_path(template) for template in config.get('mail', 'feedback_mail_templates')]

class FeedbackMailCreator:
    def __init__(self):
        self.field_substitutions = FieldSubstitutions([FieldSubstitution(':VOORNAAM:', 'voornaam'), FieldSubstitution(':TITEL:', 'titel'), FieldSubstitution(':BEDRIJF:', 'bedrijf')])
        self.htm_bodies  = self.__init__template_bodies(get_feedback_mail_templates())
        self.subject_template =  config.get('mail', 'subject')
        self.onbehalfof = config.get('mail', 'onbehalfof')
        self.outlook = OutlookMail()
        self.draft_folder_name = self.outlook.getDraftFolderName()
    def __init__template_bodies(self, templates)->dict:
        index2beoordeling = [AanvraagBeoordeling.ONVOLDOENDE, AanvraagBeoordeling.VOLDOENDE]
        result = {}
        for n, template in enumerate(templates):             
            body = ''
            with open(template) as file:
                for line in file:
                    body = body + line
            result[index2beoordeling[n]] = body 
        return result
    def __create_mail_body(self, aanvraag: AanvraagInfo)->str:
        return self.field_substitutions.translate(self.htm_bodies[aanvraag.beoordeling], voornaam=aanvraag.student.first_name, bedrijf=aanvraag.bedrijf.bedrijfsnaam, titel=aanvraag.titel) 
    def _create_mail_def(self, aanvraag: AanvraagInfo, attachment: str)->OutlookMailDef:
        subject = self.field_substitutions.translate(self.subject_template, titel=aanvraag.titel)
        return OutlookMailDef(subject=subject, mailto=aanvraag.student.email, mailbody=self.__create_mail_body(aanvraag), onbehalfof = self.onbehalfof, cc=config.get('mail', 'cc'), bcc=config.get('mail', 'bcc'), attachments=[attachment])
    def draft_mail(self, aanvraag: AanvraagInfo, attachment: str):
        self.outlook.draft_item(self._create_mail_def(aanvraag, attachment))

#OBSOLETE CLASSES START
# class FeedbackMailsCreator(AanvraagProcessor):
#     def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
#         super().__init__(storage, aanvragen)
#         self.mailer = FeedbackMailCreator()
#     def get_draft_folder_name(self):
#         return self.mailer.draft_folder_name
#     def __update_aanvraag(self, aanvraag):
#         aanvraag.status = AanvraagStatus.MAIL_READY
#         self.storage.aanvragen.update(aanvraag)
#         self.storage.commit()
#     def _process_aanvragen(self, aanvragen: list[AanvraagInfo], preview=False)->int:
#         result = 0        
#         for aanvraag in aanvragen:
#             if self.process(aanvraag, preview):
#                 result += 1        
#         return result
#     def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
#         if aanvraag.status != AanvraagStatus.GRADED:
#             return False
#         filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
#         if preview:
#             print(f'\tKlaarzetten mail ({str(aanvraag.beoordeling)}) aan "{aanvraag.student.email}" met als attachment:\n\t\t{summary_string(filename)}')
#         else:
#             self.mailer.draft_mail(aanvraag, filename)
#             logPrint(f'\tFeedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.student_name} ({aanvraag.student.email}) klaargezet in {self.get_draft_folder_name()}.')
#             self.__update_aanvraag(aanvraag)
#         return True

#     def process_all(self, filter_func = None, preview=False)->int:
#         return self._process_aanvragen(self.filtered_aanvragen(filter_func), preview=preview)

# def create_feedback_mails(storage: AAPStorage, filter_func = None, preview=False):
#     logPrint('--- Klaarzetten feedback mails...')
#     file_creator = FeedbackMailsCreator(storage)
#     n_mails = file_creator.process_all(filter_func, preview=preview)
#     klaargezet = 'klaar te zetten' if preview else 'klaargezet'    
#     logPrint(f'### {n_mails} mails {klaargezet} in Outlook {file_creator.get_draft_folder_name()}')
#     logPrint('--- Einde klaarzetten feedback mails.')
#OBSOLETE CLASSES END

class NewFeedbackMailsCreator(NewAanvraagProcessor):
    def __init__(self):
        self.mailer = FeedbackMailCreator()
    def get_draft_folder_name(self):
        return self.mailer.draft_folder_name
    def must_process(self, aanvraag: AanvraagInfo, **kwargs)->bool:
        return aanvraag.status == AanvraagStatus.GRADED
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        if preview:
            print(f'\tKlaarzetten mail ({str(aanvraag.beoordeling)}) aan "{aanvraag.student.email}" met als attachment:\n\t\t{summary_string(filename)}')
        else:
            if not Path(filename).exists():
                logError(f'Kan feedback mail voor {aanvraag} niet maken:\n\tbeoordelingbestand {filename} ontbreekt.')
                return False            
            self.mailer.draft_mail(aanvraag, filename)
            logPrint(f'\tFeedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.student_name} ({aanvraag.student.email}) klaargezet in {self.get_draft_folder_name()}.')
            aanvraag.status = AanvraagStatus.MAIL_READY
        return True

def new_create_feedback_mails(storage: AAPStorage, filter_func = None, preview=False):
    logPrint('--- Klaarzetten feedback mails...')
    file_creator = NewAanvragenProcessor(NewFeedbackMailsCreator(), storage)
    n_mails = file_creator.process(filter_func, preview=preview)
    klaargezet = 'klaar te zetten' if preview else 'klaargezet'    
    logPrint(f'### {n_mails} mails {klaargezet} in Outlook {file_creator.get_draft_folder_name()}')
    logPrint('--- Einde klaarzetten feedback mails.')

