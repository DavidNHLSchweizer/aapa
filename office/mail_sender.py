from __future__ import annotations
from enum import Enum
import win32com.client as win32

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
class OutlookMail:
    def __init__(self):
        self.outlook = win32.Dispatch('outlook.application')
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
