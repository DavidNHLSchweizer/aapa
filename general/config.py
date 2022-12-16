from dataclasses import dataclass
from aanvraag_info import AanvraagBeoordeling
from general.singleton import Singleton

@dataclass
class _AAPAConfig(Singleton):
    database_name: str = 'aapa.DB'
    form_template = r'.\templates\template 0.7.docx'
    feedback_mail_templates={AanvraagBeoordeling.ONVOLDOENDE: r'.\templates\template_afgekeurd.docx', AanvraagBeoordeling.VOLDOENDE:r'.\templates\template_goedgekeurd.docx' }

config = _AAPAConfig()    
