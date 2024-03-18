from __future__ import annotations
from argparse import ArgumentParser
from enum import Enum, auto
import tkinter
from data.general.const import MijlpaalType
from data.classes.files import File
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
    def get_file_references(self, file: File)->tuple[list[int],list[int],list[int]]:
        """ finds all references to the file in the details tables

            in theory this is always 0 or 1, but the database contains many duplicate references
            
            returns
            -------
            tuple of three lists: (ids in AANVRAGEN_DETAILS, ids in VERSLAGEN_DETAILS, ids in UNDOLOGS_DETAILS)

        """
        def get_table_refs(table: str, main_id: str, file_id: int):
            query = f'select distinct {main_id} from {table.upper()}_DETAILS where detail_id=?'
            rows = self.database._execute_sql_command(query, [file_id],True)
            return [row[0] for row in rows]
        return (get_table_refs('AANVRAGEN', 'aanvraag_id', file.id), get_table_refs('VERSLAGEN', 'verslag_id', file.id), get_table_refs('UNDOLOGS', 'log_id', file.id))

    def remove(self, remover: RemoverClass, ids: list[int], preview = True, unlink=False):
        for id in ids:
            obj = self.storage.read(remover.table_name.lower(), id)
            aanvraag_references,verslag_references,undologs_references = self.get_file_references(obj)
            refcount = len(aanvraag_references)+len(verslag_references)+len(undologs_references)
            if isinstance(remover, FileRemover) and  refcount >= 0:
                if (dialog_result:= tkinter.messagebox.askyesnocancel('Waarschuwing', f'Bestand {id} {File.display_file(obj.filename)} wordt (nog) gebruikt door {sop(refcount, 'object', 'objecten')}.\nVerwijderen kan leiden tot een inconsistente database.\nWeet je zeker dat je dit wilt doen?')) == False:                                        
                    continue
                elif dialog_result is None:
                    break
                
            #TODO: dit ook voor mijlpaal_directories en aanvragen/verslagen doen
                 
            # print(f'refcheck: {obj.id}: ({File.display_file(obj.filename)}):')
            # print(f'refcheck: aanvragen {aanvraag_references} verslagen {verslag_references} undologs {undologs_references}')
            obj_str = obj.summary() if hasattr(obj,'summary') else str(obj)
            print(f'Removing {obj_str}...')
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
        return remove_funcs.get(remove_type, None)()
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
    