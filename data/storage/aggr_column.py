from dataclasses import dataclass
from typing import Type
from data.classes.aggregator import Aggregator
from data.classes.detail_rec import DetailRec
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QIF
from data.storage.storage_base import StorageException
from data.storage.storage_const import StoredClass
from data.storage.storage_crud import CRUDs, StorageCRUD
from data.storage.table_registry import ClassAggregatorData, ClassRegistryData, class_data
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

@dataclass
class AggregatorDetail:
    aggregator_key: str
    aggregator_data: ClassAggregatorData
    attribute_name: str
    associated_class_type: StoredClass

class AggregatorDetails(dict):
    def __init__(self, class_type: Type[StoredClass], aggregator_keys: list[str], detail_rec_types: list[Type[DetailRec]]):
        self.class_type = class_type
        for aggregator_key,detail_rec_type in zip(aggregator_keys,detail_rec_types):
            data = class_data(class_type).aggregator_data
            self[detail_rec_type] = AggregatorDetail(aggregator_key,data,data.attribute,data.class_type) 
    def get_details(self, detail_rec_type: StoredClass)->AggregatorDetail:
        return self.get(detail_rec_type, None)
    
class ListAttributeCRUDs:
    def __init__(self, database: Database, details: AggregatorDetails):
        self.details = details
        self.database = database
        self.cruds = CRUDs(database, details.class_type)
    def create(self, aapa_obj: StoredClass):
        for detail_rec_type in self.details.keys():
            self.__create_details(aapa_obj, 
                                  getattr(aapa_obj, self.details.get_details(detail_rec_type).attribute_name), 
                                  getattr(aapa_obj, 'id'), detail_rec_type)
    def __create_details(self, aapa_obj: StoredClass, aggregator: Aggregator, main_id: int, 
                         detail_rec_type: Type[DetailRec]):
        detail_data = self.details.get_details(detail_rec_type)
        class_type = aggregator.get_class_type(detail_data.aggregator_key)
        detail_items = []
        associated_crud = self.cruds.get_crud(detail_data.associated_class_type)
        for item in aggregator.as_list(class_type):
            associated_crud._create_key_if_needed(item)
            associated_crud.create(item)
            detail_items.append(detail_rec_type(main_key=main_id, detail_key=item.id))
        crud = self.cruds.get_crud(detail_rec_type)
        for detail in detail_items:
            crud.create(detail)
    def read(self, aapa_obj: StoredClass):
        for detail_rec_type in self.details.keys():
            self.__read(aapa_obj, getattr(aapa_obj, self.details.get_details(detail_rec_type).attribute_name), 
                                  getattr(aapa_obj, 'id'), detail_rec_type)
    def __read(self, aapa_obj: StoredClass, aggregator: Aggregator, main_id: int, 
                         detail_rec_type: Type[DetailRec]): 
        detail_data = self.details.get_details(detail_rec_type)
        class_type = aggregator.get_class_type(detail_data.aggregator_key)
        associated_crud = self.cruds.get_crud(detail_data.associated_class_type)
        crud = self.cruds.get_crud(detail_rec_type)
        query_builder = associated_crud.query_builder
        log_debug('START ASS READ')
        column_names = crud.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        where = crud.query_builder.build_where_from_values([column_names[0]], [main_id], 
                                               flags={QIF.NO_MAP_VALUES})
        log_debug(f'where: {where}')
        rows = crud.query_builder.find_all_temp([column_names[1]], where=where)
        for row in rows:
            aggregator.add(associated_crud.read(row[0]))
        log_debug(f'END ASS READ {aggregator.as_list(class_type)}')
    def update(self, aapa_obj: StoredClass):
        raise StorageException('IMPLEMENTEER UPDATE!')
    def delete(self, aapa_obj: StoredClass):
        raise StorageException('IMPLEMENTEER DEL:ETE!')

    # def add(set_details(self, main_id: int, values: list[int]):
    #     self.aggregator.clear(self.classtype)
    #     for item in values: 
    #     self.detail_rec_type(main_key=main_id, detail_key=item.id) for item in self.items()]
        
    
    #     self.list_table,self.list_mapper_type = self.__init_list_data()
        
    # def __init_list_data(self)->tuple[TableDefinition,type[TableMapper]]:
        
    #     list_class_data = class_data(self.classtype)
    #     return list_class_data.table, list_class_data.mapper_type

    #     detail_class_data = class_data(detail_rec_type)
    #     self.detail_table = detail_class_data.table
    #     self.detail_mapper_type = detail_class_data.mapper_type


        # self.aggregator_table = 
        # self.detail_rec_type = detail_rec_type


                 
        