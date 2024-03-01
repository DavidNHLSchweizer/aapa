from data.general.details_record import DetailsRecord
from database.aapa_database import AanvraagDetailsTableDefinition, AanvragenTableDefinition
from data.classes.aanvragen import Aanvraag
from storage.general.details_crud import DetailsRecordTableMapper
from storage.general.aggregator_crud import AggregatorCRUD
from storage.general.mappers import ColumnMapper
from storage.general.CRUDs import register_crud
from storage.classes.mijlpaal_base import MijlpaalGradeableTableMapper
from storage.queries.aanvragen import AanvragenQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

class AanvragenTableMapper(MijlpaalGradeableTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvraagDetailsRecord(DetailsRecord): pass
class AanvraagDetailsTableMapper(DetailsRecordTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord):
        super().__init__(database, table, class_type, 'aanvraag_id')

register_crud(class_type=Aanvraag, 
                table=AanvragenTableDefinition(), 
                crud=AggregatorCRUD,     
                queries_type=AanvragenQueries,        
                mapper_type=AanvragenTableMapper, 
                details_record_type=AanvraagDetailsRecord,
                )
register_crud(class_type=AanvraagDetailsRecord, 
                table=AanvraagDetailsTableDefinition(), 
                mapper_type=AanvraagDetailsTableMapper, 
                autoID=False,
                main=False
                )

