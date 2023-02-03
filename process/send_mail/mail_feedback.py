from general.config import config
from process.aanvraag_processor import AanvraagProcessor
from data.classes import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileType
from data.storage import AAPStorage
from general.substitutions import FieldSubstitution, FieldSubstitutions
from process.send_mail.mail_sender import OutlookMail, OutlookMailDef
from general.log import logPrint

def init_config():
    config.set_default('mail', 'feedback_mail_templates', {str(AanvraagBeoordeling.ONVOLDOENDE): r'.\templates\template_afgekeurd.docx', str(AanvraagBeoordeling.VOLDOENDE):r'.\templates\template_goedgekeurd.docx' })
    config.set_default('mail', 'subject', 'Beoordeling aanvraag afstuderen ":TITEL:"')
    config.set_default('mail', 'cc', ['afstuderenschoolofict@nhlstenden.com'])
    config.set_default('mail', 'bcc', ['david.schweizer@nhlstenden.com', 'bas.van.hensbergen@nhlstenden.com', 'joris.lops@nhlstenden.com'])
init_config()

class FeedbackMailCreator:
    def __init__(self):
        self.field_substitutions = FieldSubstitutions([FieldSubstitution(':VOORNAAM:', 'voornaam'), FieldSubstitution(':TITEL:', 'titel'), FieldSubstitution(':BEDRIJF:', 'bedrijf')])
        self.htm_bodies  = self.__init__template_bodies(config.get('mail', 'feedback_mail_templates'))
        self.subject_template =  config.get('mail', 'subject')
        self.outlook = OutlookMail()
        self.draft_folder_name = self.outlook.getDraftFolderName()
    def __init__template_bodies(self, templates)->dict:
        result = {}
        for beoordeling in [AanvraagBeoordeling.ONVOLDOENDE, AanvraagBeoordeling.VOLDOENDE]:             
            body = ''
            with open(templates[str(beoordeling)]) as file:
                for line in file:
                    body = body + line
            result[str(beoordeling)] = body 
        return result
    def __create_mail_body(self, aanvraag: AanvraagInfo)->str:
        return self.field_substitutions.translate(self.htm_bodies[str(aanvraag.beoordeling)], voornaam=aanvraag.student.first_name, bedrijf=aanvraag.bedrijf.bedrijfsnaam, titel=aanvraag.titel)
    def _create_mail_def(self, aanvraag: AanvraagInfo, attachment: str)->OutlookMailDef:
        subject = self.field_substitutions.translate(self.subject_template, titel=aanvraag.titel)
        return OutlookMailDef(subject=subject, mailto=aanvraag.student.email, mailbody=self.__create_mail_body(aanvraag), cc=config.get('mail', 'cc'), bcc=config.get('mail', 'bcc'), attachments=[attachment])
    def draft_mail(self, aanvraag: AanvraagInfo, attachment: str):
        self.outlook.draft_item(self._create_mail_def(aanvraag, attachment))

class FeedbackMailsCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.mailer = FeedbackMailCreator()
    def get_draft_folder_name(self):
        return self.mailer.draft_folder_name
    def __update_aanvraag(self, aanvraag):
        aanvraag.status = AanvraagStatus.MAIL_READY
        self.storage.update_aanvraag(aanvraag)
        self.storage.commit()
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
                logPrint(f'Feedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.student_name} ({aanvraag.student.email}) klaargezet in {self.get_draft_folder_name()}.')
                self.__update_aanvraag(aanvraag)
            result += 1        
        return result
    def process(self, filter_func = None, preview=False)->int:
        return self._process_aanvragen(self.filtered_aanvragen(filter_func), preview=preview)

def create_feedback_mails(storage: AAPStorage, filter_func = None, preview=False):
    logPrint('--- Klaarzetten feedback mails...')
    file_creator = FeedbackMailsCreator(storage)
    n_mails = file_creator.process(filter_func, preview=preview)
    klaargezet = 'klaar te zetten' if preview else 'klaargezet'    
    logPrint(f'### {n_mails} mails {klaargezet} in Outlook {file_creator.get_draft_folder_name()}')
    logPrint('--- Einde klaarzetten feedback mails.')