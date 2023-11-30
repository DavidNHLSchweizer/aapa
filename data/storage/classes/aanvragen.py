from data.aapa_database import AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.detail_rec import DetailRec, DetailRecData
from data.classes.studenten import Student
from data.storage.detail_rec_crud import DetailRecsTableMapper
from data.storage.extended_crud import ExtendedCRUD
from data.storage.general.mappers import ColumnMapper
from data.storage.general.query_builder import QIF
from data.storage.CRUDs import CRUDhelper, register_crud
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
  
class AanvragenCRUDhelper(CRUDhelper):
    def find_kans(self, student: Student):
        CRUDhelper(self.get_crud(Student)).ensure_key(student)     
        log_debug(f'FIND KANS {student.id}')   
        result = self.find_count('student', student.id)
        log_debug(f'FOUND  KANS {result}')   
        return result
    def find_versie(self, student: Student, bedrijf: Bedrijf):
        log_debug('FIND VERSIE')
        CRUDhelper(self.get_crud(Bedrijf)).ensure_key(bedrijf)        
        CRUDhelper(self.get_crud(Student)).ensure_key(student) 
        result = self.find_max_value(attribute='versie',                                                
                                        where_attributes=['student', 'bedrijf'],
                                        where_values=[student.id, bedrijf.id])
        log_debug(f'FIND VERSIE EINDE {result}')
        return result
    def find_previous_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        if aanvraag.versie == 1:
            return None
        CRUDhelper(self.get_crud(Student)).ensure_key(aanvraag.student) 
        log_debug('FIND PREVIOUS')
        if ids := self.find_values(['versie', 'student'], 
                                   [aanvraag.versie-1, aanvraag.student.id]):
            result = self.crud.read(ids[0])
            log_debug(f'ding dong previous: {result}')
            return result    
        return None

class AanvragenFilesDetailRec(DetailRec): pass
class AanvragenFilesTableMapper(DetailRecsTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id','file_id')

register_crud(class_type=Aanvraag, 
                table=AanvraagTableDefinition(), 
                crud=ExtendedCRUD,     
                helper_type=AanvragenCRUDhelper,        
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

