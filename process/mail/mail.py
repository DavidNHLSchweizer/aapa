from enum import Enum, auto
from data.classes.action_log import ActionLog
from general.log import log_info
from general.preview import Preview, pva
from general.singular_or_plural import sop
from process.general.aanvraag_pipeline import AanvragenPipeline
from process.mail.archive_graded.archive_graded import ArchiveGradedFileProcessor
from process.mail.read_grade.read_form import ReadFormGradeProcessor
from process.mail.send_mail.create_mail import FeedbackMailProcessor
from data.storage import AAPAStorage

def process_graded(storage: AAPAStorage, filter_func = None, preview=False)->int:
    class RappPva(Enum):
        LEZEN = auto()
        ARCHIVEREN = auto()
        KLAARZETTEN = auto()
        VERWERKEN = auto()
    PVA = {RappPva.LEZEN: pva(preview, 'lezen', 'gelezen'), 
           RappPva.ARCHIVEREN: pva(preview, 'archiveren', 'gearchiveerd'),
           RappPva.KLAARZETTEN: pva(preview, 'klaarzetten', 'klaargezet'),
           RappPva.VERWERKEN: pva(preview, 'verwerken', 'verwerkt'),
        }       
    with Preview(preview, storage, 'graded'):
        log_info('--- Verwerken ingevulde beoordelingsformulieren ...', to_console=True)
        pipeline = AanvragenPipeline('Verwerken ingevulde beoordelingsformulieren', [ReadFormGradeProcessor(),  ArchiveGradedFileProcessor(storage), FeedbackMailProcessor()], storage, ActionLog.Action.MAIL)
        result = pipeline.process(preview=preview, filter_func=filter_func) 
        log_info(f'{sop(result, "aanvraag", "aanvragen")} volledig {PVA[RappPva.VERWERKEN]} (beoordeling {PVA[RappPva.LEZEN]}, {PVA[RappPva.ARCHIVEREN]} en mail {PVA[RappPva.KLAARZETTEN]}).', to_console=True)
        log_info('--- Einde verwerken beoordelingsformulieren.', to_console=True)
    return result

