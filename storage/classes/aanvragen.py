from data.general.detail_rec2 import DetailRec2, DetailRecData2
from database.aapa_database import AanvraagDetailsTableDefinition, AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.general.detail_rec import DetailRec, DetailRecData
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.detail_rec_crud2 import DetailRecsTableMapper2
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
  
class AanvragenDetailRec2(DetailRec2): pass
class AanvragenDetailsTableMapper(DetailRecsTableMapper2):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id')

register_crud(class_type=Aanvraag, 
                table=AanvraagTableDefinition(), 
                crud=ExtendedCRUD,     
                queries_type=AanvraagQueries,        
                mapper_type=AanvragenTableMapper, 
                details_data=
                    [DetailRecData2(aggregator_name='files', 
                                   detail_rec_type=AanvragenDetailRec2),
                    ]
                )
register_crud(class_type=AanvragenDetailRec2, 
                table=AanvraagDetailsTableDefinition(), 
                mapper_type=AanvragenDetailsTableMapper, 
                autoID=False,
                main=False
                )

