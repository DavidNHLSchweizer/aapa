from typing import Type
from data.classes.aggregator import Aggregator
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.query_builder import QIF
from data.storage.storage_const import AAPAClass, DetailRec, DetailRecs
from data.storage.storage_crud import StorageCRUD
from data.storage.table_registry import class_data
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

class ListAttribute:
    def __init__(self, class_type: Type[AAPAClass], aggregator_key: str, detail_rec_type: type[DetailRec]):
        self.class_type = class_type
        self.aggregator_key = aggregator_key
        self.detail_rec_type = detail_rec_type
        aggregator_data = class_data(class_type).aggregator_data               
        self.attribute_name = aggregator_data.attribute
        self.associated_class_type = aggregator_data.class_type
    
class ListAttributeCRUD(StorageCRUD):
    def __init__(self, database: Database, attribute: ListAttribute):
        self.attribute = attribute
        super().__init__(database, attribute.detail_rec_type)
        self.associated_crud = StorageCRUD(self.database, attribute.associated_class_type)
    def create(self, aapa_obj: AAPAClass):
        aggregator:Aggregator = getattr(aapa_obj, self.attribute.attribute_name)
        main_id:int = getattr(aapa_obj, 'id')
        class_type = aggregator.get_class_type(self.attribute.aggregator_key)
        details = []
        for item in aggregator.as_list(class_type):
            self.associated_crud._create_key_if_needed(item)
            self.associated_crud.create(item)
            details.append(self.attribute.detail_rec_type(main_key=main_id, detail_key=item.id))
        for detail in details:
            super().create(detail)
    def read(self, aapa_obj: AAPAClass):
        aggregator:Aggregator = getattr(aapa_obj, self.attribute.attribute_name)
        main_id:int = getattr(aapa_obj, 'id')
        class_type = aggregator.get_class_type(self.attribute.aggregator_key)
        query_builder = self.associated_crud.query_builder
        # where = query_builder.build_where_from_values(['main_key'], [main_id])
        log_debug('START ASS READ')
        column_names = self.mapper._get_columns_from_attributes(['main_key', 'detail_key'])
        where = self.query_builder.build_where_from_values([column_names[0]], [main_id], 
                                               flags={QIF.NO_MAP_VALUES})
        log_debug(f'where: {where}')
        rows = self.query_builder.find_all_temp([column_names[1]], where=where)
        for row in rows:
            aggregator.add(self.associated_crud.read(row[0]))
        log_debug(f'END ASS READ {aggregator.as_list(class_type)}')

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


                 
        