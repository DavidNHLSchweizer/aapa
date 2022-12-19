from pathlib import Path
from time import sleep
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import created_directory
from office.mail_merge import MailMerger
from data.storage import AAPStorage
from office.mail_sender import OutlookMail, OutlookMailDef
from office.word_reader import WordReader, WordReaderException
from general.log import logError, logInfo, logPrint

class FeedbackMailMerger(MailMerger):
    def __init__(self, storage: AAPStorage, template_docs:dict, default_maildef: OutlookMailDef, output_directory: str):
        super().__init__( output_directory)
        self.storage = storage
        self.template_docs = template_docs
        self.default_maildef = default_maildef
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Mail {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __convert_to_htm(self, reader: WordReader, doc_path: str): 
            try:
                reader.open_document(doc_path)
                return reader.save_as_htm()
            except WordReaderException as W:
                logError(f'Error saving to HTM: {W}')
    def __merge_document(self, aanvraag: AanvraagInfo)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.process(self.template_docs[aanvraag.beoordeling], output_filename, voornaam=aanvraag.student.first_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam)
    def __store_attachment_info(self, aanvraag: AanvraagInfo, doc_path, htm_path):
        logInfo(f'--- Start storing data for feedback mail {aanvraag}')
        aanvraag.status = AanvraagStatus.MAIL_READY
        self.storage.update_aanvraag(aanvraag)
        self.storage.create_fileinfo(FileInfo(doc_path, filetype=FileType.MAIL_DOCX, aanvraag_id=aanvraag.id))
        #TODO: dit is niet echt nodig, de DOCX kan ook wel meteen weg
        self.storage.create_fileinfo(FileInfo(htm_path, filetype=FileType.MAIL_HTM, aanvraag_id=aanvraag.id))
        self.storage.commit()
        logInfo(f'--- Succes storing data for feedback mail {aanvraag}')
    def __create_attachment(self, aanvraag: AanvraagInfo, reader: WordReader)->str:
        doc_path = self.__merge_document(aanvraag)
        htm_path = self.__convert_to_htm(reader, str(doc_path))
        logPrint(f'Document voor feedbackmail aangemaakt: {htm_path}.')
        self.__store_attachment_info(aanvraag, doc_path, htm_path) 
        return htm_path
    def __create_mail(self, aanvraag: AanvraagInfo, htm_path: str, mailer: OutlookMail):
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        with open(htm_path, mode='r') as htm_file:               
            mail_data = self.default_maildef.copy()
            mail_data.mailto=aanvraag.student.email
            mail_data.mailbody=htm_file.read()
            mail_data.attachments=[filename]
        mailer.draft_item(mail_data)
    def merge_documents(self, aanvragen: list[AanvraagInfo])->int:
        result = 0
        reader = WordReader()
        mailer = OutlookMail()
        if len(aanvragen) > 0 and not self.output_directory.is_dir():
            self.output_directory.mkdir()
            logPrint(f'Map {self.output_directory} aangemaakt.')
        for aanvraag in aanvragen:
            if aanvraag.status != AanvraagStatus.GRADED:
                continue            
            htm_path = self.__create_attachment(aanvraag, reader)
            self.__create_mail(aanvraag, htm_path, mailer)
            result += 1
        reader.close()
        return result

class FeedbackMailsCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_docs:dict, default_maildef: OutlookMailDef, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = FeedbackMailMerger(storage, template_docs, default_maildef, output_directory)
    def process(self, filter_func = None)->int:
        return self.merger.merge_documents(self.filtered_aanvragen(filter_func))

def create_feedback_mails(storage: AAPStorage, templates: dict, default_maildef: OutlookMailDef, output_directory, filter_func = None):
    logPrint('--- Klaarzetten feedback mails...')
    if created_directory(output_directory):
        logPrint(f'Map {output_directory} aangemaakt.')
    file_creator = FeedbackMailsCreator(storage, templates, default_maildef, output_directory)
    n_mails = file_creator.process(filter_func)
    logPrint(f'### {n_mails} mails klaargezet in Outlook Concepten/Drafts.')
    logPrint('--- Einde klaarzetten feedback mails.')
