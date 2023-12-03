from data.aapa_database import AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.detail_rec import DetailRec, DetailRecData
from data.classes.studenten import Student
from data.storage.detail_rec_crud import DetailRecsTableMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.mappers import ColumnMapper
from data.storage.general.query_builder import QIF
from data.storage.CRUDs import CRUDQueries, register_crud
from data.storage.classes.milestones import MilestonesCRUD, MilestonesTableMapper
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug

class AanvragenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvragenCRUDhelper(CRUDQueries):pass

class AanvragenFilesDetailRec(DetailRec): pass
class AanvragenFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id','file_id')

register_crud(class_type=Aanvraag, 
                table=AanvraagTableDefinition(), 
                crud=ExtendedCRUD,     
                queries_type=AanvragenCRUDhelper,        
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

