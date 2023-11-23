from dataclasses import dataclass
from data.classes.action_log import ActionLogAggregator
from data.classes.aggregator import Aggregator
from data.storage.storage_base import StorageBase
from data.storage.storage_const import AAPAClass, DetailRec, DetailRecs
from data.storage.storage_crud import StorageCRUD
from data.table_registry import CRUD_AggregatorData
from database.database import Database
from database.table_def import TableDefinition

   
class AggregatorStorage(StorageBase):
    # to be tested!
    def __init__(self, database: Database, class_type: AAPAClass, table: TableDefinition, aggregator_data: CRUD_AggregatorData):
        super().__init__(database, class_type=class_type, table=table)
        self.sub_crud = StorageCRUD(database, class_type=aggregator_data.aggregator.get_class_type(aggregator_data.attribute))
        self.main_table_key = aggregator_data.main_table_key
        self.attribute = aggregator_data.attribute
    def __create_detail_rec(self, aapa_obj: AAPAClass, associated_obj: AAPAClass)->DetailRec:        
        return DetailRec(main_key=getattr(aapa_obj, self.main_table_key), 
                         detail_key=getattr(associated_obj, self.sub_crud.table.key))
    def _create_detail_recs(self, aapa_obj)->DetailRecs:
        return [self.__create_detail_rec(aapa_obj, associated_obj) for associated_obj in getattr(aapa_obj, self.attribute)]
    def create(self, aapa_obj: AAPAClass):
        for detail_rec in self._create_detail_recs(aapa_obj):
            super().create(detail_rec)

   
# class CRUDbaseDetails(CRUDbase):
# #solution for n-n (or 1-1) relation association table
#     def __init__(self, database: Database):
#         a = CRUD_Aggregator(database, ActionLogAggregator())

#     # @dataclass
#     # class DetailRec:
#     #     main_key: int 
    #     detail_key: int
    # DetailRecs = list[DetailRec]

    # def __init__(self, CRUD_main: CRUDbase, detail_table: TableDefinition):
    #     assert len(detail_table.keys) == 2
    #     super().__init__(CRUD_main.database, class_type=None, table=detail_table)
    # def _get_relation_column_name(self)->str:
    #     log_debug(f'GRC: {self.table.keys[1]}')
    #     return self.table.keys[1]
    # @abstractmethod
    # def _get_objects(self, object: AAPAClass)->Iterable[AAPAClass]:
    #     return None #implement in descendants
    # def get_detail_records(self, main: AAPAClass)->DetailRecs:
    #     return [CRUDbaseDetails.DetailRec(main.id, detail.id) 
    #             for detail in sorted(self._get_objects(main), key=lambda d: d.id)]
    #             #gesorteerd om dat het anders in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    # def read(self, main_id: int)->DetailRecs:
    #     result = []
    #     if rows:=super().read(main_id, multiple=True):
    #         for row in rows:
    #             result.append(CRUDbaseDetails.DetailRec(main_key=main_id, detail_key=row[self._get_relation_column_name()]))
    #     return result
    # def update(self, main: AAPAClass):
    #     def is_changed()->bool:
    #         new_records = self.get_detail_records(main)
    #         current_records= self.read(main.id)
    #         if len(new_records) != len(current_records):
    #             return True
    #         else:
    #             for new, current in zip(new_records, current_records):
    #                 if new != current:
    #                     return True
    #         return False
    #     if is_changed():
    #         self._update(main)
    # def _update(self, main: AAPAClass):        
    #     self.delete(main.id)    
    #     self.create(main)
    # def delete_relation(self, detail_id: int):
    #     self.database._execute_sql_command(f'delete from {self.table.name} where {self._get_relation_column_name()}=?', [detail_id])        








    # def __init__(self, CRUD_main: CRUDbase, detail_table: TableDefinition):
    #     assert len(detail_table.keys) == 2
    #     super().__init__(CRUD_main.database, class_type=None, table=detail_table)
    # def _get_relation_column_name(self)->str:
    #     log_debug(f'GRC: {self.table.keys[1]}')
    #     return self.table.keys[1]
    # @abstractmethod
    # def _get_objects(self, object: AAPAClass)->Iterable[AAPAClass]:
    #     return None #implement in descendants
    # def get_detail_records(self, main: AAPAClass)->DetailRecs:
    #     return [CRUDbaseDetails.DetailRec(main.id, detail.id) 
    #             for detail in sorted(self._get_objects(main), key=lambda d: d.id)]
    #             #gesorteerd om dat het anders in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    # def read(self, main_id: int)->DetailRecs:
    #     result = []
    #     if rows:=super().read(main_id, multiple=True):
    #         for row in rows:
    #             result.append(CRUDbaseDetails.DetailRec(main_key=main_id, detail_key=row[self._get_relation_column_name()]))
    #     return result
    # def update(self, main: AAPAClass):
    #     def is_changed()->bool:
    #         new_records = self.get_detail_records(main)
    #         current_records= self.read(main.id)
    #         if len(new_records) != len(current_records):
    #             return True
    #         else:
    #             for new, current in zip(new_records, current_records):
    #                 if new != current:
    #                     return True
    #         return False
    #     if is_changed():
    #         self._update(main)
    # def _update(self, main: AAPAClass):        
    #     self.delete(main.id)    
    #     self.create(main)
    # def delete_relation(self, detail_id: int):
    #     self.database._execute_sql_command(f'delete from {self.table.name} where {self._get_relation_column_name()}=?', [detail_id])        
