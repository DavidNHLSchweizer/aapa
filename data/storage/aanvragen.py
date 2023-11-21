from typing import Any, Iterable
from data.classes.files import File, Files
from data.aapa_database import AanvraagTableDefinition
from data.classes.aanvragen import Aanvraag
from data.crud.mappers import ColumnMapper, TableMapper
from data.storage.crud_factory import registerCRUD

from data.storage.milestones import MilestonesStorage
from data.storage.storage_base import StorageCRUD
from data.storage.storage_const import DBtype
from general.log import log_debug

class AanvraagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Status(db_value)
class AanvraagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Aanvraag.Beoordeling(db_value)

class AanvragenStorage(MilestonesStorage):
    def customize_mapper(self, mapper: TableMapper):
        super().customize_mapper(mapper) #milestone
        mapper.set_mapper(AanvraagStatusColumnMapper('status'))
        mapper.set_mapper(AanvraagBeoordelingColumnMapper('beoordeling'))

registerCRUD(class_type=Aanvraag, table=AanvraagTableDefinition(), autoID=True)
