from __future__ import annotations
from enum import Enum
import win32com.client as win32
from general.singleton import Singleton
from pythoncom import CoInitialize

class OutlookApplication(Singleton):
    def __init__(self):
        CoInitialize() HIERIHIHIERHIH
        self.outlook= win32.dynamic.Dispatch('outlook.application')
        # self.outlook.visible = 0

olFormatPlain	 = 1
olFormatHTML	 = 2
olFormatRichText = 3

class MailBodyFormat(Enum):
    HTML = olFormatHTML
    RTF  = olFormatRichText
    TEXT = olFormatPlain

class OutlookMailDef:
    def __init__(self, subject:str, mailto:str, mailbody, mailType: MailBodyFormat = MailBodyFormat.HTML, 
                 onbehalfof: str = '', cc: list[str]=[], bcc: list[str]=[], attachments: list[str]=[]):
        self.subject = subject
        self.mailto = mailto
        self.mailbody = mailbody
        self.mailType = mailType 
        self.onbehalfof = onbehalfof
        self.cc = cc
        self.bcc = bcc
        self.attachments = attachments
    def copy(self)->OutlookMailDef:
        return OutlookMailDef(self.subject, self.mailto, self.mailbody, self.mailType, self.onbehalfof, self.cc, self.bcc, self.attachments)
        
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
        if maildef.onbehalfof:
            mail.SentOnBehalfOfName = maildef.onbehalfof
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
