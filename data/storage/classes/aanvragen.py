from typing import Any
from data.aapa_database import AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.classes.files import File
from data.storage.aggr_column import DetailsRecTableMapper, ListAttribute, ListAttributeCRUD
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.table_registry import ClassAggregatorData, register_table
from data.storage.classes.milestones import MilestonesStorage, MilestonesTableMapper
from data.storage.storage_const import AAPAClass, DBtype, DetailRec, KeyClass
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class AanvragenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return AanvraagStatusColumnMapper(column_name)
            case 'beoordeling': return AanvraagBeoordelingColumnMapper(column_name)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvragenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, Aanvraag)  
        self.filesCRUD = ListAttributeCRUD(database, ListAttribute(class_type=Aanvraag, aggregator_key='files', detail_rec_type=AanvragenFilesDetailRec))
        log_debug(self.filesCRUD)
    def create(self, aapa_obj: AAPAClass):
        super().create(aapa_obj)
        self.filesCRUD.create(aapa_obj)
    def read(self, key: KeyClass)->AAPAClass|list:
        if aapa_obj := super().read(key):
            self.filesCRUD.read(aapa_obj)
        return aapa_obj
    
class AanvragenFilesDetailRec(DetailRec): pass
class AanvragenFilesTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id','file_id')

register_table(class_type=Aanvraag, table=AanvraagTableDefinition(), mapper_type=AanvragenTableMapper, 
               aggregator_data=ClassAggregatorData(attribute='files', class_type=File), autoID=True)
register_table(class_type=AanvragenFilesDetailRec, table=AanvraagFilesTableDefinition(), mapper_type=AanvragenFilesTableMapper,
               autoID=True)
