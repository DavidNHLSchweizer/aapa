from dataclasses import dataclass
from pathlib import Path
from time import sleep
from data.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.aanvraag_info import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from office.mail_merge import MailMerger
from general.log import logInfo, logPrint

class BeoordelingenMailMerger(MailMerger):
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: str):
        super().__init__(output_directory)
        self.storage = storage
        self.template_doc = template_doc
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: AanvraagInfo)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.process(self.template_doc, output_filename, student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr))
    def merge_documents(self, aanvragen: list[AanvraagInfo])->int:
        result = 0
        if len(aanvragen) > 0 and not self.output_directory.is_dir():
            self.output_directory.mkdir()
            logPrint(f'Map {self.output_directory} aangemaakt.')
        for aanvraag in aanvragen:
            doc_path = self.__merge_document(aanvraag)
            logPrint(f'Formulier aangemaakt: {doc_path}.')
            aanvraag.status = AanvraagStatus.NEEDS_GRADING
            logInfo(f'--- Start storing data for form {aanvraag}')
            self.storage.update_aanvraag(aanvraag)
            self.storage.create_fileinfo(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
            self.storage.commit()
            logInfo(f'--- Succes storing data for form {aanvraag}')
            result += 1
        return result

class BeoordelingenFileCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = BeoordelingenMailMerger(storage, template_doc, output_directory)
    def process(self, filter_func = None):
        self.merger.merge_documents(self.filtered_aanvragen(filter_func))

def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None):
    logPrint('--- Maken beoordelingsformulieren...')
    file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
    file_creator.process(filter_func)
    logPrint('--- Einde maken beoordelingsformulieren.')
