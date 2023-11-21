from typing import Any
from data.crud.crud_const import AAPAClass, DBtype
from data.classes.verslagen import Verslag
from data.aapa_database import VerslagTableDefinition
from data.crud.mappers import ColumnMapper, FilenameColumnMapper, TableMapper
from data.storage.crud_factory import registerCRUD
from data.storage.milestones import MilestonesStorage


class VerslagStatusColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Status(db_value)
class VerslagBeoordelingColumnMapper(ColumnMapper):
    def map_db_to_value(self, db_value: DBtype)->Any:
        return Verslag.Beoordeling(db_value)

class VerslagenStorage(MilestonesStorage):
    def customize_mapper(self, mapper: TableMapper):
        super().customize_mapper() #milestones
        mapper.set_mapper(FilenameColumnMapper('directory'))
        mapper.set_mapper(VerslagStatusColumnMapper('status'))
        mapper.set_mapper(VerslagBeoordelingColumnMapper('beoordeling'))

registerCRUD(class_type=Verslag, table=VerslagTableDefinition(), autoID=True)