from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from main.config import ListValueConvertor, config
from general.fileutil import file_exists, from_main_path, summary_string
from general.substitutions import FieldSubstitution, FieldSubstitutions
from process.general.aanvraag_processor import AanvraagProcessor
from process.general.mail_sender import OutlookMail, OutlookMailDef
from main.log import log_error, log_print

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
        index2beoordeling = [Aanvraag.Beoordeling.ONVOLDOENDE, Aanvraag.Beoordeling.VOLDOENDE]
        result = {}
        for n, template in enumerate(templates):             
            body = ''
            with open(template, encoding='cp1252') as file:
                for line in file:
                    body = body + line
            result[index2beoordeling[n]] = body 
        return result
    def __create_mail_body(self, aanvraag: Aanvraag)->str:
        return self.field_substitutions.translate(self.htm_bodies[aanvraag.beoordeling], voornaam=aanvraag.student.first_name, bedrijf=aanvraag.bedrijf.name, titel=aanvraag.titel) 
    def _create_mail_def(self, aanvraag: Aanvraag, attachment: str)->OutlookMailDef:
        subject = self.field_substitutions.translate(self.subject_template, titel=aanvraag.titel)
        return OutlookMailDef(subject=subject, mailto=aanvraag.student.email, mailbody=self.__create_mail_body(aanvraag), onbehalfof = self.onbehalfof, cc=config.get('mail', 'cc'), bcc=config.get('mail', 'bcc'), attachments=[attachment])
    def draft_mail(self, aanvraag: Aanvraag, attachment: str):
        self.outlook.draft_item(self._create_mail_def(aanvraag, attachment))

class FeedbackMailProcessor(AanvraagProcessor):
    def __init__(self):
        self.mailer = FeedbackMailCreator()
        super().__init__(entry_states={Aanvraag.Status.ARCHIVED}, 
                         exit_state=Aanvraag.Status.MAIL_READY,
                         description='Zet feedbackmail klaar in Concepten')
    def get_draft_folder_name(self):
        return self.mailer.draft_folder_name
    def must_process(self, aanvraag: Aanvraag, preview=False, **kwargs)->bool:    
        return aanvraag.status  in {Aanvraag.Status.ARCHIVED}
    def process(self, aanvraag: Aanvraag, preview=False)->bool:
        filename = aanvraag.files.get_filename(File.Type.GRADE_FORM_PDF)
        if preview:
            log_print(f'\tKlaarzetten feedbackmail ({str(aanvraag.beoordeling)}) aan "{aanvraag.student.email}" met als attachment:\n\t\t{summary_string(filename)}')
        else:
            if not filename or not file_exists(filename):
                log_error(f'Kan feedbackmail voor {aanvraag} niet maken:\n\tbeoordelingbestand "{filename}" ontbreekt.')
                return False 
            self.mailer.draft_mail(aanvraag, filename)
            log_print(f'\tFeedbackmail ({str(aanvraag.beoordeling)}) aan {aanvraag.student.full_name} ({aanvraag.student.email}) klaargezet in {self.get_draft_folder_name()}.')
        return True
