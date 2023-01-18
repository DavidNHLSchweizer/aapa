from pathlib import Path
from data.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.aanvraag_info import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.args import ProcessMode
from general.fileutil import created_directory, file_exists
from office.mail_merge import MailMerger
from general.log import logInfo, logPrint

class MailMergeException(Exception): pass

class BeoordelingenMailMerger(MailMerger):
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: str):
        super().__init__(output_directory)
        self.storage = storage
        if not Path(template_doc).is_file():
            raise MailMergeException(f'kan template {template_doc} niet vinden.')
        self.template_doc = template_doc
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: AanvraagInfo, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.process(self.template_doc, output_filename, student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), preview=preview)
    def merge_documents(self, aanvragen: list[AanvraagInfo], preview=False)->int:
        def check_must_create_beoordeling(aanvraag: AanvraagInfo, preview=False):
            if not preview:
                if aanvraag.status in [AanvraagStatus.INITIAL, AanvraagStatus.NEEDS_GRADING]:
                    filename = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
                    if filename != None:
                        return not file_exists(filename)
                    else:
                        return True
                else:
                    return False
            else:
                filename = self.output_directory.joinpath(self.__get_output_filename(aanvraag))
                return not file_exists(filename)
        result = 0
        if len(aanvragen) > 0 and not self.output_directory.is_dir() and not preview:
            self.output_directory.mkdir()
            logPrint(f'Map {self.output_directory} aangemaakt.')
        for aanvraag in aanvragen:
            if not check_must_create_beoordeling(aanvraag, preview=preview):
                continue
            doc_path = self.__merge_document(aanvraag, preview=preview)
            aangemaakt = 'aanmaken' if preview else 'aangemaakt'
            logPrint(f'Formulier {aangemaakt}: {doc_path}.')
            aanvraag.status = AanvraagStatus.NEEDS_GRADING
            if not preview:
                logInfo(f'--- Start storing data for form {aanvraag}')
            self.storage.update_aanvraag(aanvraag)
            fileinfo = FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id)
            if self.storage.find_fileinfo(aanvraag.id, FileType.TO_BE_GRADED_DOCX):
                self.storage.update_fileinfo(fileinfo)
            else:
                self.storage.create_fileinfo(fileinfo)
            self.storage.commit()
            if not preview:
                logInfo(f'--- Succes storing data for form {aanvraag}')                
            result += 1
        return result

class BeoordelingenFileCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = BeoordelingenMailMerger(storage, template_doc, output_directory)
    def process(self, filter_func = None, preview=False)->int:
        return self.merger.merge_documents(self.filtered_aanvragen(filter_func), preview=preview)

def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, mode=ProcessMode.PROCESS, preview=False)->int:
    logPrint('--- Maken beoordelingsformulieren...')
    if not preview:
        if created_directory(output_directory):
            logPrint(f'Map {output_directory} aangemaakt.')
        storage.add_file_root(str(output_directory))
    file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
    result = file_creator.process(filter_func, preview=preview)
    logPrint('--- Einde maken beoordelingsformulieren.')
    return result
