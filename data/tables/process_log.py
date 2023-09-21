from dataclasses import dataclass
from data.classes import TSC, FileInfo
from data.tables.aanvragen import CRUD_aanvragen
from database.sqlexpr import Ops, SQLexpression as SQE
from data.AAPdatabase import ProcessLogAanvragenTableDefinition, ProcessLogTableDefinition
from data.state_log  import ProcessLog
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops
from general.keys import get_next_key

class CRUD_process_log(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ProcessLogTableDefinition())
        self._db_map['date']['db2obj'] = TSC.timestamp_to_str
        self._db_map['aantal']['attrib'] = 'nr_aanvragen'

    @staticmethod
    def action_to_value(action: ProcessLog.Action):
        return action.value
    @staticmethod
    def __int_to_bool(value: int):
        return value != 0
    # def __get_all_values(self, process_log: ProcessLog, include_key = True):
    #     result = [process_log.id] if include_key else []
    #     result.extend([process_log.description, CRUD_process_log.action_to_value(process_log.action), process_log.user, TSC.timestamp_to_str(process_log.date), 
    #                    process_log.nr_aanvragen, process_log.rolled_back])
    #     self.controle2(result, process_log,  include_key)
    #     return result
    def create(self, process_log: ProcessLog):
        process_log.id = get_next_key(ProcessLogTableDefinition.KEY_FOR_ID)
        super().create(process_log)   
    def read(self, id: int)->ProcessLog:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return ProcessLog(id=id, description=row['description'], action=ProcessLog.Action(row['action']), user=row['user'], 
                            date=TSC.str_to_timestamp(row['date']), rolled_back=CRUD_process_log.__int_to_bool(row['rolled_back']))
            #note: aantal hoeft niet te worden gelezen, komt uit aantal aanvragen (bij lezen process_log_aanvragen)
        else:
            return None
    def update(self, process_log: ProcessLog):
        super().update(columns=self._get_all_columns(False), values=self._get_all_values(process_log, False), where=SQE('id', Ops.EQ, process_log.id))
    # def delete(self, id: int):
    #     super().delete(where=SQE('id', Ops.EQ, id))
@dataclass
class ProcessLogAanvraagRec:
    log_id: int 
    aanvraag_id: int
ProcessLogAanvraagRecs = list[ProcessLogAanvraagRec]

class CRUD_process_log_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ProcessLogAanvragenTableDefinition())
    # def __get_all_values(self, log_id: int, aanvraag_id: int, include_key = True):
    #     result = [log_id, aanvraag_id] if include_key else []
    #     return result
    def get_aanvraag_records(self, process_log: ProcessLog)->ProcessLogAanvraagRecs:
        return [ProcessLogAanvraagRec(process_log.id, aanvraag.id) 
                for aanvraag in sorted(process_log.aanvragen, key=lambda a: a.id)]
                #gesorteerd om dat het anders in omgekeerde volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, process_log: ProcessLog):
        for record in self.get_aanvraag_records(process_log):
            self.database.create_record(self.table, columns=self._get_all_columns(), values=[record.log_id, record.aanvraag_id])   
    def read(self, process_log_id: int)->ProcessLogAanvraagRecs: 
        result = []
        for row in super().read(where=SQE(self.table.keys[0], Ops.EQ, process_log_id), multiple=True):
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
