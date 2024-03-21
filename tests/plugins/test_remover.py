from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
import tkinter
from data.general.aapa_class import AAPAclass
from data.general.const import MijlpaalType
from data.classes.files import File
from general.classutil import classname
from general.singular_or_plural import sop
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from process.undo.remover import AanvraagRemover, VerslagRemover, FileRemover, MijlpaalDirectoryRemover, RemoverClass, StudentDirectoryRemover
from tests.random_data import RandomData

class TestRemover(PluginBase):
    class RemoveType(Enum):
        AANVRAAG=auto()
        VERSLAG =auto()
        MIJLPAAL_DIRECTORY=auto()
        STUDENT_DIRECTORY=auto()
        FILE=auto()
        def __str__(self):
            _RT_STRS = {self.AANVRAAG: 'aanvragen', self.VERSLAG: 'verslag', self.MIJLPAAL_DIRECTORY: 'mijlpaal_directory',
                        self.STUDENT_DIRECTORY: 'student_directory', self.FILE: 'file'} 
            return _RT_STRS.get(self, '')
    RemoveChoices = {RemoveType.AANVRAAG:'A', RemoveType.VERSLAG:'V', RemoveType.MIJLPAAL_DIRECTORY:'MD', RemoveType.STUDENT_DIRECTORY: 'SD', RemoveType.FILE: 'F' }
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True
    def _get_remove_type(self, type_str: str)->RemoveType:
        for rt in self.RemoveType:
            if self.RemoveChoices.get(rt,None) == type_str:
                return rt
        return None
    def get_parser(self) -> ArgumentParser:               
        parser = super().get_parser()
        parser.add_argument('--id', type=int, action='append', help='id van te verwijderen item(s). Kan meerdere malen worden ingevoerd : --id=id1 --id=id2 etc.')
        remove_choices = self.RemoveChoices.values()
        parser.add_argument('--remove', type=str, choices=remove_choices, help=f'Type item om te verwijderen. Mogelijkheden: {[f'{self.RemoveChoices[rt]}: {str(rt)}' for rt in self.RemoveType]}.')
        parser.add_argument('-unlink', action='store_true', help='verwijder ook alle bestanden/directories uit het filesysteem.')
        return parser  
    # def get_file_references(self, file: File)->tuple[list[int],list[int],list[int]]:
    #     """ finds all references to the file in the details tables

    #         in theory this is always 0 or 1, but the database contains many duplicate references
            
    #         returns
    #         -------
    #         tuple of three lists: (ids in AANVRAGEN_DETAILS, ids in VERSLAGEN_DETAILS, ids in UNDOLOGS_DETAILS)

    #     """
    #     def get_table_refs(table: str, main_id: str, file_id: int):
    #         query = f'select distinct {main_id} from {table.upper()}_DETAILS where detail_id=?'
    #         rows = self.database._execute_sql_command(query, [file_id],True)
    #         return [row[0] for row in rows]
    #     return (get_table_refs('AANVRAGEN', 'aanvraag_id', file.id), get_table_refs('VERSLAGEN', 'verslag_id', file.id), get_table_refs('UNDOLOGS', 'log_id', file.id))
    @staticmethod
    def _obj_str(obj: AAPAclass)->str:
        return obj.summary() if hasattr(obj,'summary') else str(obj)
    def check_refcount(self, remover: RemoverClass, obj: AAPAclass)->bool:
        refcount = remover.get_refcount(self.database, obj.id)
        if refcount <= 1:
            return True
        cls_name = classname(obj)
        references = remover.get_references(self.database, obj.id)
        owner_str = "en ".join([f'{len(_refs)} {_reftype} met ids {_refs}' for _reftype,_refs in references if len(_refs) > 0])       
        if (dialog_result:= tkinter.messagebox.askyesnocancel('Waarschuwing', f'{cls_name} {self._obj_str(obj)} ({obj.id}) wordt (nog) gebruikt door {owner_str}.\nVerwijderen kan leiden tot een inconsistente database.\nWeet je zeker dat je dit wilt doen?')) is None:
            return None
        else:
            return dialog_result
    def remove(self, remover: RemoverClass, ids: list[int], preview = True, unlink=False):
        for id in ids:
            obj = self.storage.read(remover.table_name.lower(), id)
            chk_refcount = self.check_refcount(remover, obj)
            if chk_refcount == False:
                continue
            elif chk_refcount is None:
                break
            print(f'Removing {self._obj_str(obj)}...')
            remover.delete(obj)
        remover.remove(self.database, preview, unlink)
    # def remove_verslagen(self, remover: RemoverClass,ids: list[int], preview = True, unlink=False):
    #     print(f'removing verslagen: {ids} [{preview=} {unlink=}]')
    # def remove_mijlpaal_directories(self, remover: RemoverClass,ids: list[int], preview = True, unlink=False):
    #     print(f'removing mijlpaal_directories: {ids} [{preview=} {unlink=}]')
    # def remove_student_directories(self, remover: RemoverClass, ids: list[int], preview = True, unlink=False):
    #     print(f'removing student_directories: {ids}  [{preview=} {unlink=}]')
    # def remove_files(self, remover: RemoverClass, ids: list[int], preview = True, unlink=False):
    #     print(f'removing files: {ids}  [{preview=} {unlink=}]')
    def _get_remover(self, remove_type: RemoveType)->RemoverClass:
        remove_funcs = { self.RemoveType.AANVRAAG: AanvraagRemover, 
                         self.RemoveType.VERSLAG: VerslagRemover,
                         self.RemoveType.MIJLPAAL_DIRECTORY: MijlpaalDirectoryRemover,
                         self.RemoveType.STUDENT_DIRECTORY: StudentDirectoryRemover, 
                         self.RemoveType.FILE: FileRemover,
                        }
        return remove_funcs.get(remove_type, None)(include_owner_in_sql=False)
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        if not (remove_type := self._get_remove_type(kwdargs.get('remove',None))):
            print(f'Geen type om te verwijderen ingevoerd (--remove).')
            return False
        ids = kwdargs.get('id',[])
        if not ids :
            print(f'Geen ids om te verwijderen ingevoerd (--id).')
            return False
        remover = self._get_remover(remove_type)
        self.remove(remover, ids, context.preview, kwdargs.get('unlink', False))
        # remover.execute_sql(self.database, True)
        return True
    