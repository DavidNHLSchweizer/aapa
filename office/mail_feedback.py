from pathlib import Path
from time import sleep
from data.aanvraag_processor import AanvraagProcessor
from data.aanvraag_info import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from office.mail_merge import MailMerger
from data.storage import AAPStorage
from office.mail_sender import OutlookMail, OutlookMailDef
from office.word_reader import WordReader, WordReaderException
from general.log import logError, logInfo, logPrint

test = r'C:\repos\aapa\temp\Mail Hindrik Sibma(4684044) (MplusKASSA)-1.docx'
class FeedbackMailMerger(MailMerger):
    def __init__(self, storage: AAPStorage, template_docs:dict, output_directory: str):
        super().__init__( output_directory)
        self.storage = storage
        self.template_docs = template_docs
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Mail {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __convert_to_htm(self, reader: WordReader, doc_path: str): 
            try:
                # doc_path=test
                reader.open_document(doc_path)
                return reader.save_as_htm()
            except WordReaderException as W:
                logError(f'Error saving to HTM: {W}')
    def __merge_document(self, aanvraag: AanvraagInfo)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.process(self.template_docs[aanvraag.beoordeling], output_filename, voornaam=aanvraag.student.first_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam)
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
            doc_path = self.__merge_document(aanvraag)
            # print(f'{doc_path} ({doc_path.__class__})')
            htm_path = self.__convert_to_htm(reader,str(doc_path))
            logPrint(f'Document voor feedbackmail aangemaakt: {htm_path}.')
            logInfo(f'--- Start storing data for feedback mail {aanvraag}')
            self.storage.update_aanvraag(aanvraag)
            self.storage.create_fileinfo(FileInfo(doc_path, filetype=FileType.MAIL_DOCX, aanvraag_id=aanvraag.id))
            self.storage.create_fileinfo(FileInfo(htm_path, filetype=FileType.MAIL_HTM, aanvraag_id=aanvraag.id))
            self.storage.commit()
            logInfo(f'--- Succes storing data for feedback mail {aanvraag}')
            filename = aanvraag.files.get_filename(FileType.GRADED_PDF)
            with open(htm_path, mode='r') as htm_file:               
                mail_data= OutlookMailDef(subject='Beoordeling aanvraag afstuderen', mailto=aanvraag.student.email+'.test.niet.verzenden', 
                mailbody=htm_file.read(), bcc=['david.schweizer@nhlstenden.com'], attachments=[filename])
            mailer.draft_item(mail_data)
            result += 1
        reader.close()
        return result

class FeedbackMailsCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_docs:dict, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = FeedbackMailMerger(storage, template_docs, output_directory)
    def process(self, filter_func = None):
        self.merger.merge_documents(self.filtered_aanvragen(filter_func))

def create_feedback_mails(storage: AAPStorage, template_docs:dict, output_directory, filter_func = None):
    logPrint('--- Klaarzetten feecback mails...')
    file_creator = FeedbackMailsCreator(storage, template_docs, output_directory)
    file_creator.process(filter_func)
    logPrint('--- Einde klaarzetten feedback mails.')
