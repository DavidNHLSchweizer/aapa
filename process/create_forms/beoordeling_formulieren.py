from pathlib import Path
import shutil
from process.aanvraag_processor import AanvraagProcessor
from data.storage import AAPStorage
from data.classes import AanvraagInfo, AanvraagStatus, FileInfo, FileType
from general.fileutil import created_directory, file_exists, summary_string
from general.log import logError, logInfo, logPrint, logWarning
from mailmerge import MailMerge
from process.aanvraag_state_processor import NewAanvraagProcessor, NewAanvragenProcessor

from process.create_forms.difference import DifferenceProcessor

class MailMergeException(Exception): pass

class BeoordelingenMailMerger:
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: str):
        self.output_directory = Path(output_directory)
        self.storage = storage
        if not Path(template_doc).is_file():
            raise MailMergeException(f'kan template {template_doc} niet vinden.')
        self.template_doc = template_doc
        self.diff_processor = DifferenceProcessor(storage)
    def merge_document(self, template_doc: str, output_file_name: str, **kwds)->str:
        preview = kwds.pop('preview', False)
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(template_doc)
            if not preview:
                document.merge(**kwds)
                document.write(full_output_name)
            return Path(full_output_name).resolve()
        except Exception as E:
            logError(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
            return None
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: AanvraagInfo, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_name().name, timestamp=aanvraag.timestamp_str(), 
                        student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), 
                        preview=preview)
    def __copy_aanvraag_bestand(self, aanvraag: AanvraagInfo, preview = False):
        def __get_copy_filename(rootname):
            copy_filename = self.output_directory.joinpath(f'{rootname}.pdf')
            if copy_filename.exists():
                return __get_copy_filename(rootname+'(copy)')
            else:
                return copy_filename
        aanvraag_filename = aanvraag.aanvraag_source_file_name()
        copy_filename = __get_copy_filename(f'Aanvraag {aanvraag.student.student_name} ({aanvraag.student.studnr})-{aanvraag.aanvraag_nr}')
        if not preview:
            shutil.copy2(aanvraag_filename, copy_filename)
        kopied = 'Te kopiëren' if preview else 'Gekopiëerd'
        logPrint(f'\t{kopied}: aanvraag {summary_string(aanvraag_filename)} to {summary_string(copy_filename)}.')
        aanvraag.files.set_filename(FileType.COPIED_PDF, copy_filename)
    def __create_diff_file(self, aanvraag: AanvraagInfo, preview=False):
        self.diff_processor.process_aanvraag(aanvraag, self.output_directory, preview=preview)
        # def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        #     if not check_must_create_beoordeling(aanvraag, preview=preview):
        #         return False
        #     doc_path = self.__merge_document(aanvraag, preview=preview)
        #     aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        #     logPrint(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
        #     self.__copy_aanvraag_bestand(aanvraag, preview)
        #     self.__create_diff_file(aanvraag, preview)
        #     aanvraag.status = AanvraagStatus.NEEDS_GRADING
        #     if not preview:
        #         logInfo(f'--- Start storing data for form {aanvraag}')
        #     aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
        #     self.storage.aanvragen.update(aanvraag)
        #     self.storage.commit()
        #     if not preview:
        #         logInfo(f'--- Succes storing data for form {aanvraag}')                
        #     return True
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
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
                return aanvraag.status in [AanvraagStatus.INITIAL,AanvraagStatus.NEEDS_GRADING] and not file_exists(filename)
        if not check_must_create_beoordeling(aanvraag, preview=preview):
            return False
        doc_path = self.__merge_document(aanvraag, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        logPrint(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
        self.__copy_aanvraag_bestand(aanvraag, preview)
        self.__create_diff_file(aanvraag, preview)
        aanvraag.status = AanvraagStatus.NEEDS_GRADING
        if not preview:
            logInfo(f'--- Start storing data for form {aanvraag}')
        aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
        self.storage.aanvragen.update(aanvraag)
        self.storage.commit()
        if not preview:
            logInfo(f'--- Succes storing data for form {aanvraag}')                
        return True

    def merge_documents(self, aanvragen: list[AanvraagInfo], preview=False)->int:
        result = 0
        if len(aanvragen) > 0 and not self.output_directory.is_dir() and not preview:
            self.output_directory.mkdir()
            logPrint(f'Map {self.output_directory} aangemaakt.')        
        for aanvraag in aanvragen:
            if self.process(aanvraag, preview=preview):              
                result += 1
        return result

class BeoordelingenFileCreator(AanvraagProcessor):
    def __init__(self, storage: AAPStorage, template_doc: str, output_directory: Path, aanvragen: list[AanvraagInfo] = None):
        super().__init__(storage, aanvragen)
        self.merger = BeoordelingenMailMerger(storage, template_doc, output_directory)
    def process_all(self, filter_func = None, preview=False)->int:
        return self.merger.merge_documents(self.filtered_aanvragen(filter_func), preview=preview)

def create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
    logPrint('--- Maken beoordelingsformulieren en kopiëren aanvragen ...')
    logPrint(f'Formulieren worden aangemaakt in {output_directory}')
    if not preview:
        if created_directory(output_directory):
            logPrint(f'Map {output_directory} aangemaakt.')
        storage.add_file_root(str(output_directory))
    file_creator = BeoordelingenFileCreator(storage, template_doc, output_directory)
    result = file_creator.process_all(filter_func, preview=preview)
    logPrint('--- Einde maken beoordelingsformulieren.')
    return result

class BeoordelingFormsProcessor(NewAanvraagProcessor):
    def __init__(self, template_doc: str, output_directory: str):
        self.output_directory = Path(output_directory)
        if not Path(template_doc).is_file():
            raise MailMergeException(f'kan template {template_doc} niet vinden.')
        self.template_doc = template_doc
        self.diff_processor = DifferenceProcessor(storage) #TODO: dit moet worden opgelost
    def merge_document(self, template_doc: str, output_file_name: str, **kwds)->str:
        preview = kwds.pop('preview', False)
        try:
            full_output_name = self.output_directory.joinpath(output_file_name)
            document = MailMerge(template_doc)
            if not preview:
                document.merge(**kwds)
                document.write(full_output_name)
            return Path(full_output_name).resolve()
        except Exception as E:
            logError(f'Error merging document (template:{template_doc}) to {full_output_name}: {E}')
            return None
    def __get_output_filename(self, info: AanvraagInfo):
        return f'Beoordeling aanvraag {info.student} ({info.bedrijf.bedrijfsnaam})-{info.aanvraag_nr}.docx'
    def __merge_document(self, aanvraag: AanvraagInfo, preview = False)->str:
        output_filename = self.__get_output_filename(aanvraag)
        return self.merge_document(self.template_doc, output_filename, filename=aanvraag.aanvraag_source_file_name().name, timestamp=aanvraag.timestamp_str(), 
                        student=aanvraag.student.student_name,bedrijf=aanvraag.bedrijf.bedrijfsnaam,titel=aanvraag.titel,datum=aanvraag.datum_str, versie=str(aanvraag.aanvraag_nr), 
                        preview=preview)
    def __copy_aanvraag_bestand(self, aanvraag: AanvraagInfo, preview = False):
        def __get_copy_filename(rootname):
            copy_filename = self.output_directory.joinpath(f'{rootname}.pdf')
            if copy_filename.exists():
                return __get_copy_filename(rootname+'(copy)')
            else:
                return copy_filename
        aanvraag_filename = aanvraag.aanvraag_source_file_name()
        copy_filename = __get_copy_filename(f'Aanvraag {aanvraag.student.student_name} ({aanvraag.student.studnr})-{aanvraag.aanvraag_nr}')
        if not preview:
            shutil.copy2(aanvraag_filename, copy_filename)
        kopied = 'Te kopiëren' if preview else 'Gekopiëerd'
        logPrint(f'\t{kopied}: aanvraag {summary_string(aanvraag_filename)} to {summary_string(copy_filename)}.')
        aanvraag.files.set_filename(FileType.COPIED_PDF, copy_filename)
    def __create_diff_file(self, aanvraag: AanvraagInfo, preview=False):
        self.diff_processor.process_aanvraag(aanvraag, self.output_directory, preview=preview)
    def must_process(self, aanvraag: AanvraagInfo, preview=False, **kwargs)->bool:
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
            return aanvraag.status in [AanvraagStatus.INITIAL,AanvraagStatus.NEEDS_GRADING] and not file_exists(filename)
    def process(self, aanvraag: AanvraagInfo, preview=False)->bool:
        doc_path = self.__merge_document(aanvraag, preview=preview)
        aangemaakt = 'aanmaken' if preview else 'aangemaakt'
        logPrint(f'{aanvraag}\n\tFormulier {aangemaakt}: {Path(doc_path).name}.')
        self.__copy_aanvraag_bestand(aanvraag, preview)
        self.__create_diff_file(aanvraag, preview)
        aanvraag.status = AanvraagStatus.NEEDS_GRADING
        aanvraag.files.set_info(FileInfo(doc_path, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
        return True

def new_create_beoordelingen_files(storage: AAPStorage, template_doc, output_directory, filter_func = None, preview=False)->int:
    logPrint('--- Maken beoordelingsformulieren en kopiëren aanvragen ...')
    logPrint(f'Formulieren worden aangemaakt in {output_directory}')
    if not preview:
        if created_directory(output_directory):
            logPrint(f'Map {output_directory} aangemaakt.')
        storage.add_file_root(str(output_directory))
    file_creator = NewAanvragenProcessor(BeoordelingFormsProcessor(template_doc, output_directory), storage)
    result = file_creator.process(preview=preview, filter_func=filter_func)
    logPrint('--- Einde maken beoordelingsformulieren.')
    return result
