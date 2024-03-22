from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
import tkinter
from data.general.aapa_class import AAPAclass
from data.general.const import MijlpaalType
from data.classes.files import File
from general.classutil import classname
from general.singular_or_plural import sop
from main.log import log_error, log_info, log_print
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from process.undo.remover import AanvraagRemover, VerslagRemover, FileRemover, MijlpaalDirectoryRemover, RemoverClass, StudentDirectoryRemover
from tests.random_data import RandomData

class RemoverPlugin(PluginBase):
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
    @staticmethod
    def _obj_str(obj: AAPAclass)->str:
        return obj.summary() if hasattr(obj,'summary') else str(obj)
    def check_refcount(self, remover: RemoverClass, obj: AAPAclass)->bool:
        refcount = remover.get_refcount(self.database, obj)
        if refcount <= 1:
            return True
        cls_name = classname(obj)
        references = remover.get_references(self.database, obj)
        owner_str = "en ".join([f'{len(_refs)} {_reftype} met ids {_refs}' for _reftype,_refs in references if len(_refs) > 0])       
        if (dialog_result:= tkinter.messagebox.askyesnocancel('Waarschuwing', f'{cls_name} {self._obj_str(obj)} ({obj.id}) wordt (nog) gebruikt door {owner_str}.\nVerwijderen kan leiden tot een inconsistente database.\nWeet je zeker dat je dit wilt doen?')) is None:
            return None
        else:
            return dialog_result
    def remove(self, remover: RemoverClass, ids: list[int], preview = True, unlink=False):
        log_info(f'Verzamelen te verwijderen items...', to_console=True)
        for id in ids:
            obj = self.storage.read(remover.table_name.lower(), id)
            if not obj:
                log_error(f'{classname(remover.class_type)} met id {id} niet gevonden.')
                continue
            chk_refcount = self.check_refcount(remover, obj)
            if chk_refcount == False:
                continue
            elif chk_refcount is None:
                break
            log_print(f'\tte verwijderen: {self._obj_str(obj)}...')
            remover.delete(obj)
        log_info(f'Verwijderen...')
        remover.remove(self.database, preview, unlink)
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
        self.database.commit()
        return True
    