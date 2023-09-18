

from pathlib import Path

from data.classes import AanvraagInfo, AanvraagStatus, FileType


class StateLog:
    def __init__(self, initial_state: AanvraagStatus, final_state: AanvraagStatus, created_file_types: list[FileType], deleted_file_types: list[FileType]):
        self._initial_state = initial_state
        self._final_state = final_state
        self._created_file_types = created_file_types
        self._deleted_file_types = deleted_file_types
        self._created_files: list[Path] = []
        self._deleted_files: list[Path] = []
    def register_files(self, aanvraag: AanvraagInfo):
        assert aanvraag.status == self._final_state
        self._created_files = []
        self._deleted_files = []
        for filetype in self._created_file_types:
            self._created_files.append(aanvraag.files.get_filename(filetype))



class ScanStateLog(StateLog):
    def __init__(self):
        super().__init__(AanvraagStatus.INITIAL, AanvraagStatus.NEEDS_GRADING, 
                         [FileType.TO_BE_GRADED_DOCX, FileType.COPIED_PDF, FileType.DIFFERENCE_HTML],
                         [])

class MailStateLog(StateLog):
    def __init__(self):
        super().__init__(AanvraagStatus.NEEDS_GRADING, AanvraagStatus.MAIL_READY, 
                         [FileType.GRADED_DOCX, FileType.GRADED_PDF],
                         [FileType.TO_BE_GRADED_DOCX])
