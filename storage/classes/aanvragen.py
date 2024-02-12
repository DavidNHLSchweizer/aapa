from database.aapa_database import AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.general.detail_rec import DetailRec, DetailRecData
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.general.mappers import ColumnMapper
from storage.general.CRUDs import register_crud
from storage.classes.mijlpaal_base import MijlpaalGradeableTableMapper
from storage.queries.aanvragen import AanvraagQueries
from database.classes.database import Database
from database.classes.table_def import TableDefinition

class AanvragenTableMapper(MijlpaalGradeableTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvragenFilesDetailRec(DetailRec): pass
class AanvragenFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id','file_id')

register_crud(class_type=Aanvraag, 
                table=AanvraagTableDefinition(), 
                crud=ExtendedCRUD,     
                queries_type=AanvraagQueries,        
                mapper_type=AanvragenTableMapper, 
                details_data=
                    [DetailRecData(aggregator_name='files', detail_aggregator_key='files', 
                                   detail_rec_type=AanvragenFilesDetailRec),
                    ]
                )
register_crud(class_type=AanvragenFilesDetailRec, 
                table=AanvraagFilesTableDefinition(), 
                mapper_type=AanvragenFilesTableMapper, 
                autoID=False,
                main=False
                )

