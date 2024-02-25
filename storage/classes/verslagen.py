from data.general.const import MijlpaalType
from data.classes.verslagen import Verslag
from data.general.details_record import DetailsRecord
from database.aapa_database import VerslagenTableDefinition, VerslagDetailsTableDefinition
from database.classes.table_def import TableDefinition
from storage.general.details_crud import DetailsRecordTableMapper
from storage.general.aggregator_crud import AggregatorCRUD
from storage.general.mappers import ColumnMapper
from storage.general.CRUDs import register_crud
from storage.classes.mijlpaal_base import MijlpaalGradeableTableMapper
from storage.queries.verslagen import VerslagenQueries
from database.classes.database import Database



class VerslagenTableMapper(MijlpaalGradeableTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'verslag_type': return ColumnMapper(column_name=column_name,attribute_name='mijlpaal_type',db_to_obj=MijlpaalType)
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)

class VerslagDetailsRecord(DetailsRecord): pass
class VerslagDetailsTableMapper(DetailsRecordTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord):
        super().__init__(database, table, class_type, 'verslag_id')


register_crud(class_type=Verslag, 
                table=VerslagenTableDefinition(), 
                crud=AggregatorCRUD,     
                mapper_type=VerslagenTableMapper,
                queries_type=VerslagenQueries,
                details_record_type=VerslagDetailsRecord,
                )
register_crud(class_type=VerslagDetailsRecord, 
                table=VerslagDetailsTableDefinition(), 
                mapper_type=VerslagDetailsTableMapper, 
                autoID=False,
                main=False
                )
