from typing import Any
from data.aapa_database import AanvraagTableDefinition, AanvraagFilesTableDefinition
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.detail_rec import DetailRec, DetailRecData
from data.classes.studenten import Student
from data.storage.detail_rec import DetailsRecTableMapper
from data.storage.mappers import ColumnMapper
from data.storage.query_builder import QIF
from data.storage.table_registry import register_table
from data.storage.classes.milestones import MilestonesStorage, MilestonesTableMapper
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug

class AanvragenTableMapper(MilestonesTableMapper):
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case 'status': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Status)
            case 'beoordeling': return ColumnMapper(column_name=column_name, db_to_obj=Aanvraag.Beoordeling)
            case _: return super()._init_column_mapper(column_name, database)
  
class AanvragenStorage(MilestonesStorage):
    def __init__(self, database: Database):
        super().__init__(database, class_type=Aanvraag)
    def find_kans(self, student: Student):
        qb = self.query_builder
        stud_crud = self.get_crud(Student)
        stud_crud.ensure_key(student)     
        log_debug(f'FIND KANS {student.id}')   
        result = qb.find_count(where=qb.build_where_from_values(column_names=['student'], 
                                                                values=[student.id], 
                                                                flags={QIF.ATTRIBUTES, QIF.NO_MAP_VALUES}))        
        log_debug(f'FOUND  KANS {result}')   
        return result
    def find_versie(self, student: Student, bedrijf: Bedrijf):
        qb = self.query_builder
        log_debug('FIND VERSIE')
        bedr_crud = self.get_crud(Bedrijf)
        bedr_crud.ensure_key(bedrijf)        
        stud_crud = self.get_crud(Student)
        stud_crud.ensure_key(student) 
        result = qb.find_max_value(attribute='versie',                                                
                                   where=qb.build_where_from_values(column_names=['student', 'bedrijf'],
                                                                    values=[student.id, bedrijf.id], 
                                                                    flags={QIF.ATTRIBUTES,QIF.NO_MAP_VALUES})
                                                                    )
        log_debug(f'FIND VERSIE EINDE {result}')
        return result
    def find_previous_aanvraag(self, aanvraag: Aanvraag)->Aanvraag:
        if aanvraag.versie == 1:
            return None
        qb = self.query_builder
        stud_crud = self.get_crud(Student)
        stud_crud.ensure_key(aanvraag.student) 
        log_debug('FIND PREVIOUS')
        if ids := qb.find_id_from_values(['versie', 'student'], 
                                         [aanvraag.versie-1, aanvraag.student.id], 
                                         flags={QIF.ATTRIBUTES,QIF.NO_MAP_VALUES}):
            result = self.read(ids[0])
            log_debug(f'ding dong previous: {result}')
            return result    

class AanvragenFilesDetailRec(DetailRec): pass
class AanvragenFilesTableMapper(DetailsRecTableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec]):
        super().__init__(database, table, class_type, 'aanvraag_id','file_id')

register_table(class_type=Aanvraag, table=AanvraagTableDefinition(), mapper_type=AanvragenTableMapper,              
                details_data=
                    [DetailRecData(aggregator_name='files', detail_aggregator_key='files', 
                                   detail_rec_type=AanvragenFilesDetailRec),
                    ],
                autoID=True)
register_table(class_type=AanvragenFilesDetailRec, table=AanvraagFilesTableDefinition(), 
               mapper_type=AanvragenFilesTableMapper,
               autoID=True)

