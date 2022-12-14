from data.aanvraag_info import AanvraagBeoordeling
from general.args import ProcessMode
from general.config import config
from office.mail_feedback import create_feedback_mails
from office.mail_sender import OutlookMailDef
from office.read_beoordeling import read_beoordelingen_files

def init_config():
    config.set_default('mail', 'feedback_mail_templates', {str(AanvraagBeoordeling.ONVOLDOENDE): r'.\templates\template_afgekeurd.docx', str(AanvraagBeoordeling.VOLDOENDE):r'.\templates\template_goedgekeurd.docx' })
    config.set_default('mail', 'subject', 'Beoordeling aanvraag afstuderen')
    config.set_default('mail', 'cc', ['afstuderenschoolofict@nhlstenden.com'])
    config.set_default('mail', 'bcc', ['david.schweizer@nhlstenden.com', 'bas.van.hensbergen@nhlstenden.com', 'joris.lops@nhlstenden.com'])
init_config()
def __get_default_maildef():
    return OutlookMailDef(subject=config.get('mail', 'subject'), mailto='', mailbody='', cc=config.get('mail', 'cc'), bcc=config.get('mail', 'bcc'))

def template_dict_to_config(templates: dict):
    result = {}
    for key,value in templates.items():
        result[str(key)] = value
    return result
def template_dict_from_config(config_templates: dict):
    result = {}
    for key,value in config_templates.items():        
        result[AanvraagBeoordeling.from_str(key)] = value
    return result

def process_graded(storage, output_directory, filter_func = None, mode=ProcessMode.PROCESS):
    read_beoordelingen_files(storage, filter_func, mode=mode)
    create_feedback_mails(storage, template_dict_from_config(config.get('mail', 'feedback_mail_templates')), __get_default_maildef(), output_directory, filter_func, mode=mode)

