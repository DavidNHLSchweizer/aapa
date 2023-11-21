from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.crud_factory import registerCRUD
from data.storage.storage_base import StorageBase

class StudentenStorage(StorageBase):
    pass

registerCRUD(class_type=Student, table=StudentTableDefinition(), autoID=True)