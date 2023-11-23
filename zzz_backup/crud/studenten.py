from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.crud_factory import register_CRUD
from data.storage.storage_base import StorageBase

class StudentenStorage(StorageBase):
    pass

register_CRUD(class_type=Student, table=StudentTableDefinition(), autoID=True)