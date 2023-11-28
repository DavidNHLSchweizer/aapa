from copy import deepcopy
from typing import Type
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRec, DetailRecData
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QIF
from data.storage.simple_crud import SimpleCRUD
from data.storage.storage_const import StoredClass, StorageException
from data.storage.table_registry import CRUD
from database.database import Database
from database.table_def import TableDefinition
from general.classutil import classname
from general.log import log_debug

class DetailsRecTableMapper(TableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: type[DetailRec], 
                 main_key: str, detail_key:str):
        self.main_key = main_key
        self.detail_key=detail_key
        super().__init__(database, table, class_type)
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case self.main_key: return ColumnMapper(column_name,attribute_name='main_key')
            case self.detail_key: return ColumnMapper(column_name,attribute_name='detail_key')
            case  _: super()._init_column_mapper(column_name, database)
   
class DetailRecStorage(SimpleCRUD):
    def __init__(self, database: Database, main_class_type: AAPAclass):
        super().__init__(database, main_class_type)
        self.main_class_type = main_class_type
        self.details_data = self.data.details_data
        self.database = database
    def create(self, aapa_obj: StoredClass):
        log_debug(f'DRC: CREATE ({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__create_details(getattr(aapa_obj, 'id'), 
                                  getattr(aapa_obj, details.aggregator_name),
                                  details.detail_aggregator_key,
                                  details.detail_rec_type)                                       
        log_debug('DRC: END CREATE')
    def __create_details(self, main_id: int, aggregator: Aggregator, 
                         detail_aggregator_key: str, 
                         detail_rec_type: DetailRec
                         ):
        log_debug(f'DRC: CREATE DETAILS [{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_items = []
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        for item in aggregator.as_list(detail_class_type):            
            details_crud._create_key_if_needed(item)
            if not details_crud._check_already_there(item):
                details_crud.create(item)
            detail_items.append(detail_rec_type(main_key=main_id, detail_key=item.id))
        # crud = self.get_crud(detail_rec_type)
        for detail in detail_items:
            super().create(detail)
        log_debug('DRC: END CREATE DETAILS')
    def read(self, aapa_obj: StoredClass):
        log_debug(f'DRC: START READ ({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__read_details( getattr(aapa_obj, 'id'), 
                                 getattr(aapa_obj, details.aggregator_name),
                                 details.detail_aggregator_key,
                                 details.detail_rec_type)                                       
        log_debug('DRC: END READ')
    def __read_details(self, main_id: int, aggregator: Aggregator, 
                          detail_aggregator_key: str, detail_rec_type: Type[DetailRec]): 
        log_debug(f'DRC: READ DETAILS [{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        crud = self.get_crud(detail_rec_type)
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        where = crud.query_builder.build_where_from_values([column_names[0]], [main_id], 
                                               flags={QIF.NO_MAP_VALUES})
        for row in crud.query_builder.find_all([column_names[1]], where=where):
            aggregator.add(details_crud.read(row[0]))
        log_debug('DRC: END READ DETAILS')
    def update(self, aapa_obj: StoredClass):
        log_debug(f'DRC: UPDATE ({classname(aapa_obj)}: {str(aapa_obj)})')
        self.delete(deepcopy(aapa_obj))
        self.create(aapa_obj) #the simplest!
        log_debug('DRC: END UPDATE')
    def delete(self, aapa_obj: StoredClass):
        log_debug(f'DRC: DELETE ({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__delete_details( getattr(aapa_obj, 'id'), 
                                 getattr(aapa_obj, details.aggregator_name),
                                 details.detail_aggregator_key,
                                 details.detail_rec_type)                                       
        log_debug('DRC: END DELETE')
    def __delete_details(self, main_id: int, aggregator: Aggregator, 
                            detail_aggregator_key: str, detail_rec_type: Type[DetailRec]):                          
        log_debug(f'DRC: DELETE DETAILS [{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        crud = self.get_crud(detail_rec_type)
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        # column_names = ['main_key', 'detail_key']
        where = crud.query_builder.build_where_from_values([column_names[0]], [main_id], flags={QIF.NO_MAP_VALUES})
        for row in crud.query_builder.find_all([column_names[1]], where=where):
            crud.delete(crud.read(detail_rec_type(main_id,row[0]).as_list()))
            # file = details_crud.read(row[0])
            # aggregator.remove(file)
        log_debug('DRC: END DELETE DETAILS')
