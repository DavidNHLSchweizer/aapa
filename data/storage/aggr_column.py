from dataclasses import dataclass
from data.classes.aggregator import Aggregator
from data.storage.mappers import ColumnMapper, TableMapper
from data.storage.storage_const import AAPAClass, DetailRec, DetailRecs
from data.storage.storage_crud import StorageCRUD
from data.storage.table_registry import class_data
from database.database import Database
from database.table_def import TableDefinition






class ListAttribute:
    def __init__(self, attribute_name: str, aggregator_key: str, 
                        detail_rec_type: type[DetailRec]):
        self.attribute_name = attribute_name        
        self.aggregator_key = aggregator_key
        # self.class_type = self.aggregator.get_class_type(self.aggregator_key)
        self.detail_rec_type = detail_rec_type
        super().__init__()
    # def items(self)->list[AAPAClass]:
    #     return self.aggregator.as_list(self.class_type)
    # def get_details(self, aggregator: Aggregator, main_id: int)->DetailRecs:
    #     return [self.detail_rec_type(main_key=main_id, detail_key=item.id) for item in self.items()]
    
class ListAttributeCrud(StorageCRUD):
    def __init__(self, database: Database, attribute: ListAttribute):
        self.attribute = attribute
        super().__init__(database, attribute.detail_rec_type)
    def create(self, aapa_obj: AAPAClass):
        aggregator:Aggregator = getattr(aapa_obj, self.attribute.attribute_name)
        main_id:int = getattr(aapa_obj, 'id')
        class_type = aggregator.get_class_type(self.attribute.aggregator_key)
        details = [self.attribute.detail_rec_type(main_key=main_id, detail_key=item.id) for item in aggregator.as_list(class_type)]
                    
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


        self.aggregator_table = 
        self.detail_rec_type = detail_rec_type


                 
        