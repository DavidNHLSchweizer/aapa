from typing import Type
from data.classes.aapa_class import AAPAclass
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRec, DetailRecData
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QIF
from data.storage.storage_const import StoredClass, StorageException
from data.storage.storage_crud import CRUDs
from database.database import Database
from database.table_def import TableDefinition
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
   
class DetailRecCRUDs:
    def __init__(self, database: Database, main_class_type: AAPAclass, detail_rec_data:list[DetailRecData]):
        self.main_class_type = main_class_type
        self.detail_rec_data = detail_rec_data
        self.database = database
        self.cruds = CRUDs(database, self.main_class_type)   
    def create(self, aapa_obj: StoredClass):
        for details in self.detail_rec_data:
            self.__create_details(getattr(aapa_obj, 'id'), 
                                  getattr(aapa_obj, details.aggregator_name),
                                  details.detail_aggregator_key,
                                  details.detail_rec_type)                                       
    def __create_details(self, main_id: int, aggregator: Aggregator, 
                         detail_aggregator_key: str, 
                         detail_rec_type: DetailRec
                         ):
        detail_items = []
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.cruds.get_crud(detail_class_type)
        for item in aggregator.as_list(detail_class_type):            
            details_crud._create_key_if_needed(item)
            if not details_crud._check_already_there(item):
                details_crud.create(item)
            detail_items.append(detail_rec_type(main_key=main_id, detail_key=item.id))
        crud = self.cruds.get_crud(detail_rec_type)
        for detail in detail_items:
            crud.create(detail)
    def read(self, aapa_obj: StoredClass):
        for details in self.detail_rec_data:
            self.__read_details( getattr(aapa_obj, 'id'), 
                                 getattr(aapa_obj, details.aggregator_name),
                                 details.detail_aggregator_key,
                                 details.detail_rec_type)                                       
    def __read_details(self, main_id: int, aggregator: Aggregator, 
                          detail_aggregator_key: str, detail_rec_type: Type[DetailRec]): 
        detail_class_type = aggregator.get_class_type(detail_aggregator_key)
        details_crud = self.cruds.get_crud(detail_class_type)
        crud = self.cruds.get_crud(detail_rec_type)
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        where = crud.query_builder.build_where_from_values([column_names[0]], [main_id], 
                                               flags={QIF.NO_MAP_VALUES})
        for row in crud.query_builder.find_all_temp([column_names[1]], where=where):
            aggregator.add(details_crud.read(row[0]))
    def update(self, aapa_obj: StoredClass):
        raise StorageException('IMPLEMENTEER UPDATE!')
    def delete(self, aapa_obj: StoredClass):
        raise StorageException('IMPLEMENTEER DEL:ETE!')

         
        