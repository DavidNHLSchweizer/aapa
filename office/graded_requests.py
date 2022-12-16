from data.aanvraag_info import AanvraagBeoordeling
from general.config import config
from office.mail_feedback import create_feedback_mails
from office.mail_sender import OutlookMailDef
from office.read_beoordeling import read_beoordelingen_files

def init_config():
    config.set_default('mail', 'feedback_mail_templates', {AanvraagBeoordeling.ONVOLDOENDE: r'.\templates\template_afgekeurd.docx', AanvraagBeoordeling.VOLDOENDE:r'.\templates\template_goedgekeurd.docx' })
    config.set_default('mail', 'subject', 'Beoordeling aanvraag afstuderen')
    config.set_default('mail', 'cc', ['afstuderenchoolofict@nhlstenden.com'])
    config.set_default('mail', 'bcc', ['david.schweizer@nhlstenden.com'])
init_config()
def __get_default_maildef():
    return OutlookMailDef(subject=config.get('mail', 'subject'), mailto='', mailbody='', cc=config.get('mail', 'cc'), bcc=config.get('mail', 'bcc'))

def process_graded(storage, output_directory, filter_func = None):
    read_beoordelingen_files(storage, filter_func)
    create_feedback_mails(storage, config.get('mail', 'feedback_mail_templates'), __get_default_maildef(), output_directory, filter_func)
