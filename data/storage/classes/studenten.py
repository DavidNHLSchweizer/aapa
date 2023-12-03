from data.aapa_database import StudentTableDefinition
from data.classes.studenten import Student
from data.storage.CRUDs import register_crud
from data.storage.queries.studenten import StudentQueries

register_crud(class_type=Student, 
                table=StudentTableDefinition(),
                queries_type=StudentQueries
                )