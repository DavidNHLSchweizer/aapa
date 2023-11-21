from dataclasses import dataclass
from pydoc import classname
from typing import Iterable
from data.classes.bedrijven import Bedrijf
from data.aapa_database import AanvraagTableDefinition, StudentMilestonesTableDefinition, VerslagTableDefinition
from data.classes.files import File
from data.classes.milestones import Milestone, StudentMilestones
from data.classes.studenten import Student
from data.crud.mappers import TableMapper, TimeColumnMapper
from data.crud.crud_base import CRUD, AAPAClass, CRUDColumnMapper, CRUDbase
from data.crud.crud_factory import createCRUD
from data.storage.storage_base import StorageBase, StorageCRUD
from database.database import Database
from database.table_def import TableDefinition
from general.log import log_debug

class MilestonesStorage(StorageBase):
    # semi-abstract base class for AANVRAGEN and VERSLAGEN, handles the common parts
    def customize_mapper(self, mapper: TableMapper):
        mapper.set_mapper(TimeColumnMapper('datum'))
        mapper.set_mapper(CRUDColumnMapper('stud_id', attribute_name='student', crud=createCRUD(self.database, Student)))
        mapper.set_mapper(CRUDColumnMapper('bedrijf_id', attribute_name='bedrijf', crud=createCRUD(self.database, Bedrijf)))


    def __load(self, milestone_id: int, filetypes: set[File.Type], crud_files: StorageCRUD)->Iterable[File]:
        log_debug(f'__load: {classname(self)} - {milestone_id}: {filetypes}')
        self.get_crud(File)
        if file_IDs := crud_files.query_builder.find_id_from_values(attributes=['aanvraag_id', 'filetype'], values = [milestone_id, filetypes]):
            log_debug(f'found: {file_IDs}')
            result = [crud_files.read(id) for id in file_IDs]
            return result
        return []
    def find_all(self, aanvraag_id: int)->Files:
        log_debug('find_all')
        result = Files(aanvraag_id)        
        filetypes = {ft for ft in File.Type if ft != File.Type.UNKNOWN}
        result.reset_file(filetypes)
        if files := self.__load(aanvraag_id, filetypes):
            for file in files:
                result.set_file(file)
        return result        



    def __read_all_filtered(self, milestones: Iterable[Milestone], filter_func = None)->Iterable[Milestone]:
        if not filter_func:
            return milestones
        else:
            return list(filter(filter_func, milestones))
    def __read_all_all(self, filter_func = None)->Iterable[Milestone]:

        sql = SQLselect(self.table_name, query=f'select id from {self.table_name} where status != ?')
        if row:= self.database._execute_sql_command(sql.query, [Aanvraag.Status.DELETED], True):            
            return self.__read_all_filtered([self.read(r['id']) for r in row], filter_func=filter_func)
        else:
            return None
    def __read_all_states(self, states:set[int], filter_func = None)->Iterable[Milestone]:
        if rows:= self.query_builder.find_id_from_values(['status'], [states]):
            return self.__read_all_filtered([self.read(r['id']) for r in rows], filter_func=filter_func)
        return None
    def read_all(self, filter_func = None, states:set[int]=None)->Iterable[Milestone]:
        if not states:
            return self.__read_all_all(filter_func=filter_func)        
        else: 
            return self.__read_all_states(filter_func=filter_func, states=states)








class CRUD_student_milestones(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, StudentMilestonesTableDefinition(), class_type=StudentMilestones, autoID=True)

@dataclass
class MilestoneDetailRelationRec:
    ms_id: int 
    rel_id: int
    rel_type: int

MilestoneDetailRelationRecs = list[MilestoneDetailRelationRec]

class CRUD_milestones_details(CRUDbase):
    def __init__(self, database: Database, relation_table: TableDefinition):
        super().__init__(database, relation_table, None)
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        return None #implement in descendants
    def get_relation_records(self, milestones: StudentMilestones)->MilestoneDetailRelationRecs:
        return [MilestoneDetailRelationRec(milestones.id, object.id, object.milestone_type) 
                for object in sorted(self._get_objects(milestones), key=lambda o: o.id)]
                #gesorteerd om dat het anders - misschien - in onlogische volgorde wordt gedaan en vergelijking ook lastig wordt (zie update)
    def create(self, milestones: StudentMilestones):
        for record in self.get_relation_records(milestones):
            self.database.create_record(self.table, 
                                        columns=self._helper.get_all_columns(), 
                                        values=[record.ms_id, record.rel_id, record.rel_type])   
    # def read(self, milestones_id: int)->MilestoneDetailRelationRecs:
    #     result = []
    #     if rows:=super().read(milestones_id, multiple=True):
    #         for row in rows:
    #             result.append(ActionLogRelationRec(log_id=action_log_id, rel_id=row[self._get_relation_column_name()]))
    #     return result


class CRUD_milestone_details_aanvragen(CRUD_milestones_details):
    def __init__(self, database: Database):
        super().__init__(database, AanvraagTableDefinition())
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        return None #milestones.get({Verslag.Type.AANVRAAG})

class CRUD_milestone_details_verslagen(CRUD_milestones_details):
    def __init__(self, database: Database):
        super().__init__(database, VerslagTableDefinition())
    def _get_objects(self, milestones: StudentMilestones)->Iterable[Milestone]:
        # types = {milestone_type for milestone_type in Verslag.Type 
        #             if milestone_type not in {Verslag.Type.UNKNOWN, 
        #                                       Verslag.Type.AANVRAAG}}
        return None
        return milestones.get(types)
