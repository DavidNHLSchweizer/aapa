from dataclasses import dataclass
from data.tables.aanvragen import CRUD_aanvragen
from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import ProcessLogAanvragenTableDefinition, ProcessLogTableDefinition
from data.classes.process_log  import ProcessLog
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key
from general.timeutil import TSC

def BTV(value: bool)->int:
    return 1 if value else 0
def VTB(value: int)->bool:
    return value == 1

class CRUD_process_log(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ProcessLogTableDefinition(), ProcessLog)
        self._db_map['date']['db2obj'] = TSC.str_to_timestamp
        self._db_map['date']['obj2db'] = TSC.timestamp_to_str
        self._db_map['rolled_back']['db2obj'] = VTB
        self._db_map['rolled_back']['obj2db'] = BTV        
    def create(self, process_log: ProcessLog):
        process_log.id = get_next_key(ProcessLogTableDefinition.KEY_FOR_ID)
        super().create(process_log)                          

@dataclass
class ProcessLogAanvraagRec:
    log_id: int 
    aanvraag_id: int
ProcessLogAanvraagRecs = list[ProcessLogAanvraagRec]

class CRUD_process_log_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ProcessLogAanvragenTableDefinition(), None) #TBD
    def get_aanvraag_records(self, process_log: ProcessLog)->ProcessLogAanvraagRecs:
        return [ProcessLogAanvraagRec(process_log.id, aanvraag.id) 
                for aanvraag in sorted(process_log.aanvragen, key=lambda a: a.id)]
                #gesorteerd om dat het anders in omgekeerde volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, process_log: ProcessLog):
        for record in self.get_aanvraag_records(process_log):
            self.database.create_record(self.table, columns=self._get_all_columns(), values=[record.log_id, record.aanvraag_id])   
    def read(self, process_log_id: int)->ProcessLogAanvraagRecs: 
        result = []
        for row in super().read(process_log_id, multiple=True):
            result.append(ProcessLogAanvraagRec(log_id=process_log_id, aanvraag_id=row['aanvraag_id']))
        return result
    def update(self, process_log: ProcessLog):
        def is_changed()->bool:
            new_records = self.get_aanvraag_records(process_log)
            current_records= self.read(process_log.id)
            if len(new_records) != len(current_records):
                return True
            else:
                for new, current in zip(new_records, current_records):
                    if new != current:
                        return True
            return False
        if is_changed():
            self._update(process_log)
    def _update(self, process_log: ProcessLog):        
        self.delete(process_log.id)    
        self.create(process_log)
    # def delete(self, process_log_id: int):
    #     super().delete(where=SQE('log_id', Ops.EQ, process_log_id))
