from pathlib import Path
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagBeoordeling, AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import created_directory, path_with_suffix
from office.beoordeling_formulieren import MailMergeException
from office.mail_merge import MailMerger
from data.storage import AAPStorage
from office.mail_sender import OutlookMail, OutlookMailDef
from office.word_processor import WordDocument, WordReaderException
from general.log import logError, logInfo, logPrint

class FeedbackMailMerger(MailMerger):
    def __init__(self, storage: AAPStorage, template_docs:dict, default_maildef: OutlookMailDef, output_directory: str):
        super().__init__( output_directory)
        self.storage = storage
        for beoordeling in [AanvraagBeoordeling.ONVOLDOENDE, AanvraagBeoordeling.VOLDOENDE]:
            if not Path(template_doc:=template_docs[beoordeling]).is_file():
                raise MailMergeException(f'kan feedback mail template ({template_doc}) voor "{beoordeling}" niet vinden.')
        self.template_docs = template_docs
        self.default_maildef = default_maildef
        self.mailer = OutlookMail()
        self.draft_folder_name = self.mailer.getDraftFolderName()
        self.reader = WordDocument()
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Mail {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __convert_to_htm(self, doc_path: str, preview=False): 
        htm_path = path_with_suffix(doc_path, '.htm')
        if preview:
            return htm_path
        else:
            try:
                with self.reader.open_document(doc_path) as document:
                    return document.save_as_htm(htm_path)
            except WordReaderException as W:
                logError(f'Error saving to HTM {htm_path}: {W}')
    def __merge_document(self, aanvraag: AanvraagInfo, preview=False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        if preview:
            return self.output_directory.joinpath(output_filename)
        else:
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
    def __create_attachment(self, aanvraag: AanvraagInfo, preview=False)->str:
        doc_path = self.__merge_document(aanvraag, preview=preview)
        htm_path = self.__convert_to_htm(str(doc_path), preview=preview)
        aangemaakt = 'aan te maken' if preview else 'aangemaakt'
        logPrint(f'Document voor feedbackmail {aangemaakt}: {htm_path}.')
        self.__store_attachment_info(aanvraag, doc_path, htm_path) 
        return htm_path
    def __create_mail(self, aanvraag: AanvraagInfo, htm_path: str, preview=False):
        filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
        if preview:
            print(f'\tKlaarzetten mail: bestemming {aanvraag.student.email}   attachment: {filename}')
        else:
            with open(htm_path, mode='r') as htm_file:               
                mail_data = self.default_maildef.copy()
                mail_data.mailto=aanvraag.student.email
                mail_data.mailbody=htm_file.read()
                mail_data.attachments=[filename]
            self.mailer.draft_item(mail_data)
    def merge_documents(self, aanvragen: list[AanvraagInfo], preview=False)->int:
        result = 0        
        if len(aanvragen) > 0 and not self.output_directory.is_dir():
            if not preview:
                self.output_directory.mkdir()
                logPrint(f'Map {self.output_directory} aangemaakt.')
            else:
                print(f'\taanmaken map {self.output_directory}.')
        for aanvraag in aanvragen:
            if aanvraag.status != AanvraagStatus.GRADED:
                continue            
            htm_path = self.__create_attachment(aanvraag, preview=preview)
            self.__create_mail(aanvraag, htm_path, preview=preview)
            result += 1        
        return result

class FeedbackMailsCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_docs:dict, default_maildef: OutlookMailDef, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = FeedbackMailMerger(storage, template_docs, default_maildef, output_directory)
    def get_draft_folder_name(self):
        return self.merger.draft_folder_name
    def process(self, filter_func = None, preview=False)->int:
        return self.merger.merge_documents(self.filtered_aanvragen(filter_func), preview=preview)

def create_feedback_mails(storage: AAPStorage, templates: dict, default_maildef: OutlookMailDef, output_directory, filter_func = None, preview=False):
    logPrint('--- Klaarzetten feedback mails...')
    if preview:
        if not Path(output_directory).is_dir():
            print(f'Map {output_directory} aan te maken.')
    else:
        if created_directory(output_directory):
            logPrint(f'Map {output_directory} aangemaakt.')
    storage.add_file_root(str(output_directory))
    file_creator = FeedbackMailsCreator(storage, templates, default_maildef, output_directory)
    n_mails = file_creator.process(filter_func, preview=preview)
    klaargezet = 'klaar te zetten' if preview else 'klaargezet'    
    logPrint(f'### {n_mails} mails {klaargezet} in Outlook {file_creator.get_draft_folder_name()}')
    logPrint('--- Einde klaarzetten feedback mails.')
