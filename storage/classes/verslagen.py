from data.general.const import MijlpaalType
from data.classes.verslagen import Verslag
from data.general.detail_rec import DetailRec, DetailRecData
from database.aapa_database import VerslagFilesTableDefinition, VerslagTableDefinition
from database.classes.table_def import TableDefinition
from storage.general.detail_rec_crud import DetailRecsTableMapper
from storage.general.extended_crud import ExtendedCRUD
from storage.general.mappers import ColumnMapper
from storage.general.CRUDs import register_crud
from storage.classes.mijlpaal_base import MijlpaalGradeableTableMapper
from storage.queries.verslagen import VerslagQueries
from database.classes.database import Database



class VerslagenTableMapper(MijlpaalGradeableTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'verslag_type': return ColumnMapper(column_name=column_name,attribute_name='mijlpaal_type',db_to_obj=MijlpaalType)
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Verslag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)

class VerslagenFilesDetailRec(DetailRec): pass
class VerslagenFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'verslag_id','file_id')


register_crud(class_type=Verslag, 
                table=VerslagTableDefinition(), 
                crud=ExtendedCRUD,     
                mapper_type=VerslagenTableMapper,
                queries_type=VerslagQueries,
                details_data=
                    [DetailRecData(aggregator_name='files', detail_aggregator_key='files', 
                                   detail_rec_type=VerslagenFilesDetailRec),
                    ]
                )
register_crud(class_type=VerslagenFilesDetailRec, 
                table=VerslagFilesTableDefinition(), 
                mapper_type=VerslagenFilesTableMapper, 
                autoID=False,
                main=False
                )