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
    def __get_all_columns(self, include_key = True):
        result = ['id'] if include_key else []
        result.extend(['description', 'activity', 'user', 'date', 'aantal'])
        return result
    @staticmethod
    def __activity_to_value(activity: ProcessLog.Activity):
        return activity.value
    def __get_all_values(self, process_log: ProcessLog, include_key = True):
        result = [process_log.id] if include_key else []
        result.extend([process_log.description, CRUD_process_log.__activity_to_value(process_log.activity), process_log.user, TSC.timestamp_to_str(process_log.date), process_log.nr_aanvragen])
        return result
    def create(self, process_log: ProcessLog):
        process_log.id = get_next_key(ProcessLogTableDefinition.KEY_FOR_ID)
        super().create(columns=self.__get_all_columns(), values=self.__get_all_values(process_log))   
    def read(self, id: int)->ProcessLog:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return ProcessLog(id=id, description=row['description'], activity=ProcessLog.Activity(row['activity']), user=row['user'], date=TSC.str_to_timestamp(row['date'])) 
            #note: aantal hoeft niet te worden gelezen, komt uit aantal aanvragen (bij lezen process_log_aanvragen)
        else:
            return None
    def update(self, process_log: ProcessLog):
        super().update(columns=self.__get_all_columns(False), values=self.__get_all_values(process_log, False), where=SQE('id', Ops.EQ, process_log.id))
    def delete(self, id: int):
        super().delete(where=SQE('id', Ops.EQ, id))
@dataclass
class ProcessLogAanvraagRec:
    log_id: int 
    aanvraag_id: int
ProcessLogAanvraagRecs = list[ProcessLogAanvraagRec]

class CRUD_process_log_aanvragen(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, ProcessLogAanvragenTableDefinition())
        self.crud_aanvragen = CRUD_aanvragen(database)
    def __get_all_columns(self, include_key = True):
        result = ['log_id', 'aanvraag_id'] if include_key else []
        return result
    def __get_all_values(self, log_id: int, aanvraag_id: int, include_key = True):
        result = [log_id, aanvraag_id] if include_key else []
        return result
    def get_aanvraag_records(self, process_log: ProcessLog)->ProcessLogAanvraagRecs:
        return [ProcessLogAanvraagRec(process_log.id, aanvraag.id) 
                for aanvraag in sorted(process_log.aanvragen, key=lambda a: a.id)]
                #gesorteerd om dat het anders in omgekeerde volgorde wordt gedaan
    def create(self, process_log: ProcessLog):
        for record in self.get_aanvraag_records(process_log):
            super().create(columns=self.__get_all_columns(), values=self.__get_all_values(record.log_id, record.aanvraag_id))   
    def read(self, process_log_id: int)->list[ProcessLogAanvraagRecs]: 
        result = []
        for row in super().read(where=SQE('log_id', Ops.EQ, process_log_id), multiple=True):
            result.append(ProcessLogAanvraagRec(log_id=process_log_id, aanvraag_id = self.crud_aanvragen.read(row['aanvraag_id'])))
        return result
    def update(self, process_log: ProcessLog):
        self.delete(process_log.id)    
        self.create(self.get_aanvraag_records(process_log))
    def delete(self, process_log_id: int):
        super().delete(where=SQE('log_id', Ops.EQ, process_log_id))
