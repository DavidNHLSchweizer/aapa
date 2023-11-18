from data.aapa_database import BaseDirsTableDefinition
from data.classes.base_dirs import BaseDir
from data.crud.mappers import FilenameColumnMapper
from data.crud.crud_base import CRUD, CRUDbase
from data.crud.crud_factory import registerCRUD

class CRUD_basedirs(CRUDbase):
    def customize_mapper(self):
        self.set_mapper(FilenameColumnMapper('directory'))
    def _post_action(self, basedir: BaseDir, crud_action: CRUD)->BaseDir:        
        match crud_action:
            case CRUD.INIT:pass
            case _: pass
        return basedir

registerCRUD(CRUD_basedirs, class_type=BaseDir, table=BaseDirsTableDefinition(),  autoID=True)