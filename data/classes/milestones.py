from data.classes.files import File, Files
from data.classes.studenten import Student
from database.dbConst import EMPTY_ID
from general.timeutil import TSC

class Milestone:            
    def __init__(self, type_description: str, student:Student, status=0, beoordeling = '', titel='', id=EMPTY_ID):
        self.type_description = type_description
        self._id = id
        self.student = student
        self.titel = titel
        self._files = Files(id)
        self.status = status
        self.beoordeling = beoordeling
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        self._id = value
        self._files.aanvraag_id = value
    @property
    def files(self)->Files:
        return self._files
    @files.setter
    def files(self, files: Files):
        for ft in File.Type:
            if ft != File.Type.UNKNOWN:
                self.files.set_file(files.get_file(ft))
    def register_file(self, filename: str, filetype: File.Type):
        self.files.set_file(File(filename, timestamp=TSC.AUTOTIMESTAMP, filetype=filetype, aanvraag_id=self.id))
    def unregister_file(self, filetype: File.Type):
        self.files.reset_file(filetype)
