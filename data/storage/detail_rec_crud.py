from copy import deepcopy
from typing import Type
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRec
from data.storage.CRUDs import CRUD, CRUDQueries
from data.classes.mappers import ColumnMapper
from data.storage.general.table_mapper import TableMapper
from data.storage.general.query_builder import QIF
from data.storage.general.storage_const import StoredClass
from database.database import Database
from database.table_def import TableDefinition
from general.classutil import classname
from general.log import log_debug

class DetailRecsTableMapper(TableMapper):
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
   
class DetailRecsCRUD(CRUD):
    def __init__(self, database: Database, main_class_type: AAPAclass):
        super().__init__(database, main_class_type)
        self.main_class_type = main_class_type
        self.details_data = self._data.details_data
        self.database = database
    def __db_log(self, function: str, params: str=''):
        log_debug(f'DRC({classname(self)}): {function}{(" - " + params) if params else ""}')        
    def create(self, aapa_obj: StoredClass):
        self.__db_log('CREATE', f'({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__create_details(getattr(aapa_obj, 'id'), 
                                  getattr(aapa_obj, details.aggregator_name),
                                  details.detail_aggregator_key,
                                  details.detail_rec_type)                                       
        self.__db_log('END CREATE')
    def __create_details(self, main_id: int, aggregator: Aggregator, 
                         detail_aggregator_key: str, 
                         detail_rec_type: DetailRec
                         ):
        self.__db_log('CREATE DETAILS', f'[{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_items = []
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        for item in aggregator.as_list(detail_class_type):            
            CRUDQueries(details_crud).create_key_if_needed(item)
            if not CRUDQueries(details_crud).check_already_there(item) or \
                CRUDQueries(details_crud).is_changed(item):
                details_crud.create(item)
            detail_items.append(detail_rec_type(main_key=main_id, detail_key=item.id))
        detail_rec_crud = self.get_crud(detail_rec_type)
        for detail in detail_items:
            detail_rec_crud.create(detail)
        self.__db_log('END CREATE DETAILS')
    def read(self, aapa_obj: StoredClass):
        self.__db_log('START READ', f'({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__read_details( getattr(aapa_obj, 'id'), 
                                 getattr(aapa_obj, details.aggregator_name),
                                 details.detail_aggregator_key,
                                 details.detail_rec_type)                                       
        self.__db_log('END READ')
    def __read_details(self, main_id: int, aggregator: Aggregator, 
                          detail_aggregator_key: str, detail_rec_type: Type[DetailRec]): 
        self.__db_log('READ DETAILS', f'[{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        crud = self.get_crud(detail_rec_type)
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        qb = crud.query_builder
        where = qb.build_where_from_values([column_names[0]], [main_id], 
                                               flags={QIF.NO_MAP_VALUES})
        rows = qb.find_all([column_names[1]], where=where)
        aggregator.add(details_crud.read_many({row[0] for row in rows}))
        self.__db_log('END READ DETAILS')
    def update(self, aapa_obj: StoredClass):
        self.__db_log('UPDATE', f'({classname(aapa_obj)}: {str(aapa_obj)})')
        self.delete(deepcopy(aapa_obj))
        self.create(aapa_obj) #the simplest!
        self.__db_log('END UPDATE')
    def delete(self, aapa_obj: StoredClass):
        self.__db_log('DELETE', f'({classname(aapa_obj)}: {str(aapa_obj)})')
        for details in self.details_data:
            self.__delete_details( getattr(aapa_obj, 'id'), 
                                 getattr(aapa_obj, details.aggregator_name),
                                 details.detail_aggregator_key,
                                 details.detail_rec_type)                                       
        self.__db_log('END DELETE')
    def __delete_details(self, main_id: int, aggregator: Aggregator, 
                            detail_aggregator_key: str, detail_rec_type: Type[DetailRec]):                          
        self.__db_log('DELETE DETAILS', f'[{classname(detail_rec_type)}] ({main_id=} {detail_aggregator_key=})')
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.get_crud(detail_class_type)
        crud = self.get_crud(detail_rec_type)
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        # column_names = ['main_key', 'detail_key']
        qb = crud.query_builder
        where = qb.build_where_from_values([column_names[0]], [main_id], flags={QIF.NO_MAP_VALUES})
        for row in qb.find_all([column_names[1]], where=where):
            crud.delete(crud.read(detail_rec_type(main_id,row[0]).as_list()))
        self.__db_log('END DELETE DETAILS')
