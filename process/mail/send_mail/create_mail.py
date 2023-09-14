from pathlib import Path
from data.classes import AanvraagInfo
from general.config import ListValueConvertor, config
from general.fileutil import from_main_path, summary_string
from data.classes import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileType
from data.storage import AAPStorage
from general.preview import pva
from general.singular_or_plural import sop
from general.substitutions import FieldSubstitution, FieldSubstitutions
from process.general.aanvraag_processor import AanvraagProcessor, AanvragenProcessor
from process.general.mail_sender import OutlookMail, OutlookMailDef
from general.log import log_error, log_print

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

class FeedbackMailProcessor(AanvraagProcessor):
    def __init__(self):
        self.mailer = FeedbackMailCreator()
    def get_draft_folder_name(self):
        return self.mailer.draft_folder_name
    def must_process(self, aanvraag: AanvraagInfo, **kwargs)->bool:        
        return aanvraag.status == AanvraagStatus.GRADED
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        if preview:
            log_print(f'\tKlaarzetten feedbackmail ({str(aanvraag.beoordeling)}) aan "{aanvraag.student.email}" met als attachment:\n\t\t{summary_string(filename)}')
        else:
            if not Path(filename).exists():
                log_error(f'Kan feedbackmail voor {aanvraag} niet maken:\n\tbeoordelingbestand {filename} ontbreekt.')
                return False            
            self.mailer.draft_mail(aanvraag, filename)
            log_print(f'\tFeedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.student_name} ({aanvraag.student.email}) klaargezet in {self.get_draft_folder_name()}.')
            aanvraag.status = AanvraagStatus.MAIL_READY
        return True

def create_feedback_mails(storage: AAPStorage, filter_func = None, preview=False):
    log_print('--- Klaarzetten feedback mails...')
    processor = AanvragenProcessor(FeedbackMailProcessor(), storage)
    n_mails = processor.process_aanvragen(filter_func, preview=preview)
    log_print(f'### {n_mails} {sop(n_mails,"mail", "mails")} {pva(preview, "klaar te zetten", "klaargezet")} in Outlook {processor.get_draft_folder_name()}')
    log_print('--- Einde klaarzetten feedback mails.')

