from pathlib import Path
import shutil
from typing import Iterable
from process.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.classes import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import file_exists, summary_string
from general.log import log_error, log_info, log_print, log_warning
from general.fileutil import created_directory, file_exists, summary_string
from general.log import log_error, log_info, log_print, log_warning
from mailmerge import MailMerge
from process.create_forms.copy_aanvraag import CopyAanvraagProcessor
from process.create_forms.create_diff_file import NewDifferenceProcessor
from process.new_aanvraag_processor import NewAanvraagProcessor, NewAanvragenProcessor

class MailMergeException(Exception): pass

# class BeoordelingenMailMerger:
#     def __init__(self, storage: AAPStorage, template_doc: str, output_directory: str):
#         self.output_directory = Path(output_directory)
#         self.storage = storage
#         if not Path(template_doc).is_file():
#             raise MailMergeException(f'kan template {template_doc} niet vinden.')
#         self.template_doc = template_doc
#         self.diff_processor = DifferenceProcessor(storage)
#     def merge_document(self, template_doc: str, output_file_name: str, **kwds)->str:
#         preview = kwds.pop('preview', False)
#         try:
#             full_output_name = self.output_directory.joinpath(output_file_name)
#             document = MailMerge(template_doc)
#             if not preview:
#                 document.merge(**kwds)
#                 document.write(full_output_name)
#             return Path(full_output_name).resolve()
#         except Exception as E:
#             log_error(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
#             return None
#     def __get_output_filename(self, info: AanvraagInfo):
#         return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
#     def __merge_document(self, aanvraag: AanvraagInfo, preview = False)->str:
#         output_filename = self.__get_output_filename(aanvraag)
#         return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_name().name, timestamp=aanvraag.timestamp_str(), 
#                         student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), 
#                         preview=preview)
#     def __copy_aanvraag_bestand(self, aanvraag: AanvraagInfo, preview = False):
#         def __get_copy_filename(rootname):
#             copy_filename = self.output_directory.joinpath(f'{rootname}.pdf')
#             if copy_filename.exists():
#                 return __get_copy_filename(rootname+'(copy)')
#             else:
#                 return copy_filename
#         aanvraag_filename = aanvraag.aanvraag_source_file_name()
#         copy_filename = __get_copy_filename(f'Aanvraag {aanvraag.student.student_name} ({aanvraag.student.studnr})-{aanvraag.aanvraag_nr}')
#         if not preview:
#             shutil.copy2(aanvraag_filename, copy_filename)
#         kopied = 'Te kopiëren' if preview else 'Gekopiëerd'
#         log_print(f'\t{kopied}: aanvraag {summary_string(aanvraag_filename)} to {summary_string(copy_filename)}.')
#         aanvraag.files.set_filename(FileType.COPIED_PDF, copy_filename)
#     def __create_diff_file(self, aanvraag: AanvraagInfo, preview=False):
#         self.diff_processor.process_aanvraag(aanvraag, self.output_directory, preview=preview)
#         # def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
#         #     if not check_must_create_beoordeling(aanvraag, preview=preview):
#         #         return False
#         #     doc_path = self.__merge_document(aanvraag, preview=preview)
#         #     aangemaakt = 'aanmaken' if preview else 'aangemaakt'
#         #     log_print(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
#         #     self.__copy_aanvraag_bestand(aanvraag, preview)
#         #     self.__create_diff_file(aanvraag, preview)
#         #     aanvraag.status = AanvraagStatus.NEEDS_GRADING
#         #     if not preview:
#         #         log_info(f'--- Start storing data for form {aanvraag}')
#         #     aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
#         #     self.storage.aanvragen.update(aanvraag)
#         #     self.storage.commit()
#         #     if not preview:
#         #         log_info(f'--- Succes storing data for form {aanvraag}')                
#         #     return True
#     def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
#         def check_must_create_beoordeling(aanvraag: AanvraagInfo, preview=False):
#             if aanvraag.status in [AanvraagStatus.INITIAL]:
#                 generated_filename = self.output_directory.joinpath(self.__get_output_filename(aanvraag))
#                 if preview:
#                     check_exist_warning([generated_filename])
#                     return True
#                 else:
#                     check_exist_warning([aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX), generated_filename])
#                     return True
#             else:
#                 filename = self.output_directory.joinpath(self.__get_output_filename(aanvraag))
#                 return aanvraag.status in [AanvraagStatus.INITIAL,AanvraagStatus.NEEDS_GRADING] and not file_exists(filename)
#         if not check_must_create_beoordeling(aanvraag, preview=preview):
#             return False
#         doc_path = self.__merge_document(aanvraag, preview=preview)
#         aangemaakt = 'aanmaken' if preview else 'aangemaakt'
#         log_print(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
#         self.__copy_aanvraag_bestand(aanvraag, preview)
#         self.__create_diff_file(aanvraag, preview)
#         aanvraag.status = AanvraagStatus.NEEDS_GRADING
#         if not preview:
#             log_info(f'--- Start storing data for form {aanvraag}')
#         aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
#         self.storage.aanvragen.update(aanvraag)
#         self.storage.commit()
#         if not preview:
#             log_info(f'--- Succes storing data for form {aanvraag}')                
#         return True

#     def merge_documents(self, aanvragen: list[AanvraagInfo], preview=False)->int:
#         result = 0
#         if len(aanvragen) > 0 and not self.output_directory.is_dir() and not preview:
#             self.output_directory.mkdir()
#             log_print(f'Map {self.output_directory} aangemaakt.')        
#         for aanvraag in aanvragen:
#             if self.process(aanvraag, preview=preview):              
#                 result += 1
#         return result

# class BeoordelingenFileCreator(AanvraagProcessor):
#     def __init__(self, storage: AAPStorage, template_doc: str, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
#         super().__init__(storage, aanvragen)
#         self.merger = BeoordelingenMailMerger(storage, template_doc, output_directory)
#     def process_all(self, filter_func = None, preview=False)->int:
#         return self.merger.merge_documents(self.filtered_aanvragen(filter_func), preview=preview)

# def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
#     log_print('--- Maken beoordelingsformulieren en kopiëren aanvragen ...')
#     log_print(f'Formulieren worden aangemaakt in {output_directory}')
#     if not preview:
#         if created_directory(output_directory):
#             log_print(f'Map {output_directory} aangemaakt.')
#         storage.add_file_root(str(output_directory))
#     file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
#     result = file_creator.process_all(filter_func, preview=preview)
#     log_print('--- Einde maken beoordelingsformulieren.')
#     return result

class BeoordelingFormsCreator(NewAanvraagProcessor):
    def __init__(self, template_doc: str, output_directory: str):
        self.output_directory = Path(output_directory)
        if not Path(template_doc).exists():
            raise MailMergeException(f'kan template {template_doc} niet vinden.')
        self.template_doc = template_doc
    def merge_document(self, template_doc: str, output_file_name: str, **kwds)->str:
        preview = kwds.pop('preview', False)
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(template_doc)
            if not preview:
                document.merge(**kwds)
                document.write(full_output_name)
            return full_output_name.resolve()
        except Exception as E:
            log_error(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
            return None
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: AanvraagInfo, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_name().name, timestamp=aanvraag.timestamp_str(), 
                        student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), 
                        preview=preview)
    def must_process(self, aanvraag: AanvraagInfo, preview=False, **kwargs)->bool:
        log_info(f'aanvraag status {aanvraag.status}')
        if not aanvraag.status in [AanvraagStatus.INITIAL, AanvraagStatus.NEEDS_GRADING]:
            return False
        if not preview:
            filename = aanvraag.files.get_filename(FileType.TO_BE_GRADED_DOCX)
            if filename != None:
                return not file_exists(filename)                
            else:
                return True
        else:
            filename = self.output_directory.joinpath(self.__get_output_filename(aanvraag))
            return not file_exists(filename)
    def process(self, aanvraag: AanvraagInfo, preview=False, previous_aanvraag: AanvraagInfo=None, **kwdargs)->bool:
        doc_path = self.__merge_document(aanvraag, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        log_print(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
        aanvraag.status = AanvraagStatus.NEEDS_GRADING
        aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
        return True

def new_create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
    log_info('--- Maken beoordelingsformulieren en kopiëren aanvragen ...')
    log_info(f'Formulieren worden aangemaakt in {output_directory}')
    if not preview:
        if created_directory(output_directory):
            log_print(f'Map {output_directory} aangemaakt.')
        storage.add_file_root(str(output_directory))
    file_creator = NewAanvragenProcessor([BeoordelingFormsCreator(template_doc, output_directory), 
                                            CopyAanvraagProcessor(output_directory), 
                                            NewDifferenceProcessor(storage.aanvragen.read_all(), output_directory)], storage)
    result = file_creator.process_aanvragen(preview=preview, filter_func=filter_func, output_directory=output_directory) 
    log_info('--- Einde maken beoordelingsformulieren.')
    return result
