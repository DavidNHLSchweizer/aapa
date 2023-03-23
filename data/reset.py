from abc import ABC, abstractmethod
from pathlib import Path
from data.classes import AUTOTIMESTAMP, FileInfo, FileType, AanvraagStatus, AanvraagInfo, AanvraagBeoordeling
from general.log import logError
from storage import AAPStorage
from general.preview import Preview

RESETCODE = ':'
class ResetCommandBase(ABC):
    def __init__(self, reset_arg: str, expected_code: str):
        self.valid = self.parse(self.__parse_valid(reset_arg, expected_code))
    def __parse_valid(self, reset_arg: str, expected_code: str)->str:        
        words = reset_arg.split(RESETCODE)
        if len(words) != 2:
            return None
        if words[0].lower() == expected_code.lower():
            return words[1]
        return None
    @abstractmethod
    def parse(self, reset_arg_parameters: str)->bool:
        pass
    @abstractmethod
    def process(self, storage: AAPStorage, preview = True)->bool:
        pass

class ResetAanvraagForMailCommand(ResetCommandBase):
    def __init__(self, reset_arg: str):
        super().__init__(reset_arg, 'mail')
    def parse(self, reset_arg_parameters: str)->bool:
        try:
            self.aanvraag_id = int(reset_arg_parameters)
        except ValueError:
            self.aanvraag_id = None
            return False
        return True
    def process(self, storage: AAPStorage, preview = True)->bool:
        with Preview(preview):
            if not (aanvraag := storage.read_aanvraag(self.aanvraag_id)):
                logError(f'Aanvraag met aanvraag_id {self.aanvraag_id} kan niet worden geladen.')
                return False
            aanvraag.status = AanvraagStatus.NEEDS_GRADING
            aanvraag.beoordeling = AanvraagBeoordeling.TE_BEOORDELEN
            if (info := aanvraag.files.get_info(FileType.GRADED_DOCX)):
                aanvraag.files.set_info(FileInfo(info.filename, timestamp=AUTOTIMESTAMP, filetype=FileType.TO_BE_GRADED_DOCX, aanvraag_id=aanvraag.id))
                storage.update_fileinfo(aanvraag.files.get_info(FileType.TO_BE_GRADED_DOCX))
                aanvraag.files.reset_info(FileType.GRADED_DOCX)
                storage.update_fileinfo(aanvraag.files.get_info(FileType.GRADED_DOCX))
            if (info := aanvraag.files.get_info(FileType.GRADED_PDF)):
                Path(info.filename).unlink(missing_ok=True)
                aanvraag.files.reset_info(FileType.GRADED_PDF)         
                storage.update_fileinfo(aanvraag.files.get_info(FileType.GRADED_PDF))
            storage.update_aanvraag(aanvraag)
            storage.commit()


        



