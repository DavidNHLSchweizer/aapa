from copy import deepcopy
from data.general.aapa_class import AAPAclass
from data.general.aggregator import Aggregator
from data.general.class_codes import ClassCodes
from data.general.details_record import DetailsRecord
from storage.general.CRUDs import CRUD, CRUDQueries
from storage.general.mappers import ColumnMapper
from storage.general.table_mapper import TableMapper
from storage.general.query_builder import QIF
from storage.general.storage_const import StorageException, StoredClass
from database.classes.database import Database
from database.classes.table_def import TableDefinition
from general.classutil import classname
from main.log import log_debug

class DetailsRecordTableMapper(TableMapper):
    def __init__(self, database: Database, table: TableDefinition, class_type: DetailsRecord, main_id: str):
        self.main_id = main_id
        super().__init__(database, table, class_type)
    def _init_column_mapper(self, column_name: str, database: Database=None)->ColumnMapper:
        match column_name:
            case self.main_id: return ColumnMapper(column_name,attribute_name='main_id')
            case  _: return super()._init_column_mapper(column_name, database)
   
class DetailsCRUD(CRUD):
    """ CRUD to read details tables 
    
        DetailsCRUD should not be called separately but only from AggregatorCRUD (mapping the "master" table).
        
        The DetailsCRUD functions will be called from the corresponding CRUD function with a "full" initialized AAPA object.

        The AAPA object is assumed to have an Aggregator attribute. The DetailsCRUD will read the DetailRecords from the 
        Details table and store them in the Aggregator, or write the correct DetailRecords to the Details table from 
        the Aggregator. The rest is "magic".

    """
    def __init__(self, database: Database, main_class_type: AAPAclass):
        super().__init__(database, main_class_type)
        self.main_class_type = main_class_type
        self.details_record_type = self._data.details_record_type
        self.crud = self.get_crud(self.details_record_type)
        self._aggregator_name = None
        self.main_column_name = self.crud.mapper._get_columns_from_attributes(['main_id'])[0]
        self.database = database
    def __db_log(self, function: str, params: str=''):
        log_debug(f'DRC({classname(self)}): {function}{(" - " + params) if params else ""}')        
    def get_aggregator_name(self, aapa_obj: AAPAclass)->str:
        if self._aggregator_name:
            return self._aggregator_name
        else:
            for attribute in dir(aapa_obj):
                if attribute[0] == '_': continue
                if isinstance(getattr(aapa_obj,attribute), Aggregator):
                    self._aggregator_name = attribute
                    break
            if not self._aggregator_name:                
                raise StorageException(f'Aggregator not found in object {aapa_obj}.')
            return self._aggregator_name
    def aggregator(self, aapa_obj: AAPAclass)->Aggregator:
        return getattr(aapa_obj, self.get_aggregator_name(aapa_obj))       
    def _get_class_codes(self, aggregator: Aggregator)->list[str]:
        return [ClassCodes.classtype_to_code(class_type) for class_type in aggregator.class_types()]
    def create(self, owning_obj: StoredClass):
        self.__db_log('CREATE', f'({classname(owning_obj)}: {str(owning_obj)}) [{classname(self.details_record_type)}] ({owning_obj.id=})')
        aggregator = self.aggregator(owning_obj)
        for code in self._get_class_codes(aggregator):
            details_class_type = ClassCodes.code_to_classtype(code)
            details_crud = self.get_crud(details_class_type)
            for details_item in aggregator.as_list(details_class_type):     
                CRUDQueries(details_crud).create_key_if_needed(details_item)
                if not CRUDQueries(details_crud).check_already_there(details_item) or \
                    CRUDQueries(details_crud).is_changed(details_item):
                    details_crud.create(details_item)
                self.crud.create(self.details_record_type(main_id=owning_obj.id, detail_id=details_item.id, class_code=code))
        self.__db_log('END CREATE')
    def read(self, owning_obj: StoredClass):
        self.__db_log('START READ', f'({classname(owning_obj)}: {str(owning_obj)}) [{classname(self.details_record_type)}] ({owning_obj.id=})')
        aggregator = self.aggregator(owning_obj)
        read_dict = { class_code: {'ids': set(), 'crud': self.get_crud(ClassCodes.code_to_classtype(class_code))} 
                     for class_code in self._get_class_codes(aggregator)}
        qb = self.crud.query_builder
        where = qb.build_where_from_values([self.main_column_name], [owning_obj.id], flags={QIF.NO_MAP_VALUES})
        for row in qb.find_all(['detail_id','class_code'], where=where):
            read_dict[row['class_code']]['ids'].add(row['detail_id'])
        for entry in read_dict.values():            
            aggregator.add(entry['crud'].read_many(entry['ids']))
        self.__db_log('END READ')
    def update(self, owning_obj: StoredClass):
        self.__db_log('UPDATE', f'({classname(owning_obj)}: {str(owning_obj)})')
        #the simplest: just remove all details and create them again
        #else you need to find out differences between existing details and current details
        self.delete(deepcopy(owning_obj))
        self.create(owning_obj) 
        self.__db_log('END UPDATE')
    def delete(self, owning_obj: StoredClass):
        self.__db_log('DELETE', f'({classname(owning_obj)}: {str(owning_obj)}) [{classname(self.details_record_type)}] ({owning_obj.id=})')
        qb = self.crud.query_builder
        where = qb.build_where_from_values([self.main_column_name], [owning_obj.id], flags={QIF.NO_MAP_VALUES})
        for row in qb.find_all(['detail_id', 'class_code'], where=where):
            self.crud.delete(self.details_record_type(owning_obj.id,row['detail_id'], row['class_code']))
        self.__db_log('END DELETE')
