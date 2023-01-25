from __future__ import annotations
from enum import Enum
import win32com.client as win32
from aanvraag_info import AanvraagBeoordeling, AanvraagInfo
from general.config import config
from general.singleton import Singleton
from general.substitutions import FieldSubstitution, FieldSubstitutions

class OutlookApplication(Singleton):
    def __init__(self):
        self.outlook= win32.dynamic.Dispatch('outlook.application')
        # self.outlook.visible = 0

def init_config():
    config.set_default('mail', 'feedback_mail_templates', {str(AanvraagBeoordeling.ONVOLDOENDE): r'.\templates\template_afgekeurd.docx', str(AanvraagBeoordeling.VOLDOENDE):r'.\templates\template_goedgekeurd.docx' })
    config.set_default('mail', 'subject', 'Beoordeling aanvraag afstuderen ":TITEL:"')
    config.set_default('mail', 'cc', ['afstuderenschoolofict@nhlstenden.com'])
    config.set_default('mail', 'bcc', ['david.schweizer@nhlstenden.com', 'bas.van.hensbergen@nhlstenden.com', 'joris.lops@nhlstenden.com'])
init_config()

olFormatPlain	 = 1
olFormatHTML	 = 2
olFormatRichText = 3

class MailBodyFormat(Enum):
    HTML = olFormatHTML
    RTF  = olFormatRichText
    TEXT = olFormatPlain

class OutlookMailDef:
    def __init__(self, subject:str, mailto:str, mailbody, mailType: MailBodyFormat = MailBodyFormat.HTML, 
                cc: list[str]=[], bcc: list[str]=[], attachments: list[str]=[]):
        self.subject = subject
        self.mailto = mailto
        self.mailbody = mailbody
        self.mailType = mailType 
        self.cc = cc
        self.bcc = bcc
        self.attachments = attachments
    def copy(self)->OutlookMailDef:
        return OutlookMailDef(self.subject, self.mailto, self.mailbody, self.mailType,self.cc, self.bcc, self.attachments)
        
olMailItem = 0
olSave = 0
olFolderDrafts = 16
class OutlookMail:
    def __init__(self):
        self._outlook_app = OutlookApplication()        
    @property
    def outlook(self):
        return self._outlook_app.outlook
    def __createItem(self, maildef: OutlookMailDef):
        mail = self.outlook.CreateItem(olMailItem)
        mail.Subject = maildef.subject
        mail.To = maildef.mailto
        match maildef.mailType:
            case MailBodyFormat.HTML:
                mail.HTMLBody=maildef.mailbody
            case MailBodyFormat.RTF:
                mail.RTFBody=maildef.mailbody
            case _: mail.Body=maildef.mailbody
        mail.CC = ';'.join(maildef.cc)
        mail.BCC = ';'.join(maildef.bcc)
        for attachment in maildef.attachments:
            mail.Attachments.Add(attachment)
        return mail
    def send_item(self, maildef: OutlookMailDef):
        self.__createItem(maildef).Send()
    def draft_item(self, maildef: OutlookMailDef):
        self.__createItem(maildef).Close(olSave)
    def getDraftFolderName(self):
        return self.outlook.GetNameSpace('MAPI').GetDefaultFolder(olFolderDrafts)

class FeedbackMailCreator:
    def __init__(self):
        self.field_substitutions = FieldSubstitutions([FieldSubstitution(':VOORNAAM:', 'voornaam'), FieldSubstitution(':TITEL:', 'titel'), FieldSubstitution(':BEDRIJF:', 'bedrijf')])
        self.htm_bodies  = self.__init__template_bodies(config.get('mail', 'feedback_mail_templates'))
        self.subject_template =  config.get('mail', 'subject')
        print(self.subject_template)
        self.outlook = OutlookMail()
        self.draft_folder_name = self.outlook.getDraftFolderName()
    def __init__template_bodies(self, templates)->dict:
        result = {}
        print (templates)
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
