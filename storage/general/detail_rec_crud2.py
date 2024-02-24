from copy import deepcopy
from typing import Type
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.general.class_codes import ClassCodes
from data.general.detail_rec import DetailRec
from data.general.detail_rec2 import DetailRec2
from storage.general.CRUDs import CRUD, CRUDQueries
from storage.general.mappers import ColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.query_builder import QIF
from storage.general.storage_const import StoredClass
from database.classes.database import Database
from database.classes.table_def import TableDefinition
from general.classutil import classname
from main.log import log_debug

class DetailRecsTableMapper2(TableMapper):
    def __init__(self, database: Database, table: TableDefinition, 
                 class_type: type[DetailRec2], 
                 main_id: str):
        self.main_id = main_id
        super().__init__(database, table, class_type)
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case self.main_id: return ColumnMapper(column_name,attribute_name='main_id')
            case  _: return super()._init_column_mapper(column_name, database)
   
class DetailRecsCRUD2(CRUD):
    def __init__(self, database: Database, main_class_type: AAPAclass):
        super().__init__(database, main_class_type)
        self.main_class_type = main_class_type
        self.details_data = self._data.details_data
        self.database = database
    def __db_log(self, function: str, params: str=''):
        log_debug(f'DRC({classname(self)}): {function}{(" - " + params) if params else ""}')        
    def __get_class_codes(self, aggregator: Aggregator)->list[str]:
        return [ClassCodes.classtype_to_code(class_type) for class_type in aggregator.class_types()]
    def create(self, aapa_obj: StoredClass):
        main_id = getattr(aapa_obj, 'id', None)
        detail_rec_type = self.details_data[0].detail_rec_type
        self.__db_log('CREATE', f'({classname(aapa_obj)}: {str(aapa_obj)}) [{classname(detail_rec_type)}] ({main_id=})')
        aggregator = getattr(aapa_obj, self.details_data[0].aggregator_name)
        crud = self.get_crud(detail_rec_type)
        for code in self.__get_class_codes(aggregator):
            class_type = ClassCodes.code_to_classtype(code)
            details_crud = self.get_crud(class_type)
            for item in aggregator.as_list(class_type):     
                CRUDQueries(details_crud).create_key_if_needed(item)
                if not CRUDQueries(details_crud).check_already_there(item) or \
                    CRUDQueries(details_crud).is_changed(item):
                    details_crud.create(item)
                crud.create(detail_rec_type(main_id=main_id, detail_id=item.id, class_code=code))
        self.__db_log('END CREATE')
    def read(self, aapa_obj: StoredClass):
        main_id = getattr(aapa_obj, 'id', None)
        detail_rec_type = self.details_data[0].detail_rec_type
        self.__db_log('START READ', f'({classname(aapa_obj)}: {str(aapa_obj)}) [{classname(detail_rec_type)}] ({main_id=})')
        aggregator = getattr(aapa_obj, self.details_data[0].aggregator_name)
        crud = self.get_crud(detail_rec_type)
        main_column_name = crud.mapper._get_columns_from_attributes(['main_id'])[0]
        read_dict = { class_code: {'ids': set(), 'crud': self.get_crud(ClassCodes.code_to_classtype(class_code))} 
                     for class_code in self.__get_class_codes(aggregator)}
        qb = crud.query_builder
        where = qb.build_where_from_values([main_column_name], [main_id], flags={QIF.NO_MAP_VALUES})
        for row in qb.find_all(['detail_id','class_code'], where=where):
            read_dict[row['class_code']]['ids'].add(row['detail_id'])
        for entry in read_dict.values():            
            aggregator.add(entry['crud'].read_many(entry['ids']))
        self.__db_log('END READ')
    def update(self, aapa_obj: StoredClass):
        self.__db_log('UPDATE', f'({classname(aapa_obj)}: {str(aapa_obj)})')
        self.delete(deepcopy(aapa_obj))
        self.create(aapa_obj) #the simplest!
        self.__db_log('END UPDATE')
    def delete(self, aapa_obj: StoredClass):
        main_id = getattr(aapa_obj, 'id', None)
        detail_rec_type = self.details_data[0].detail_rec_type
        self.__db_log('DELETE', f'({classname(aapa_obj)}: {str(aapa_obj)}) [{classname(detail_rec_type)}] ({main_id=})')
        crud = self.get_crud(detail_rec_type)
        qb = crud.query_builder
        main_column_name = crud.mapper._get_columns_from_attributes(['main_id'])[0]
        where = qb.build_where_from_values([main_column_name], [main_id], flags={QIF.NO_MAP_VALUES})
        for row in qb.find_all(['detail_id', 'class_code'], where=where):
            crud.delete(detail_rec_type(main_id,row['detail_id'], row['class_code']))
        self.__db_log('END DELETE')
