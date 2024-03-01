from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.classes.studenten import Student
from storage.general.mappers import ColumnMapper, TimeColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.aggregator_crud import AggregatorCRUD
from storage.general.storage_const import StoredClass
from storage.general.CRUDs import create_crud, CRUDColumnMapper
from database.classes.database import Database

class MijlpaalGradeableTableMapper(TableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'datum': return TimeColumnMapper(column_name)
            case 'stud_id': 
                return CRUDColumnMapper(column_name, attribute_name='student', crud=create_crud(database, Student))
            case 'bedrijf_id': 
                return CRUDColumnMapper(column_name, attribute_name='bedrijf', crud=create_crud(database, Bedrijf))
            case _: return super()._init_column_mapper(column_name, database)

