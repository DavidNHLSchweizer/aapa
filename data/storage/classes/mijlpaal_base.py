from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from data.classes.mappers import ColumnMapper, TimeColumnMapper
from data.storage.general.table_mapper import TableMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.storage_const import StoredClass
from data.storage.CRUDs import create_crud, CRUDColumnMapper
from database.database import Database

class MijlpaalGradeableTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper(column_name, attribute_name='student', crud=create_crud(database, Student))
            case 'bedrijf_id': 
                return CRUDColumnMapper(column_name, attribute_name='bedrijf', crud=create_crud(database, Bedrijf))
            case _: return super()._init_column_mapper(column_name, database)

