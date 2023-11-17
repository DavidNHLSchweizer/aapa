from dataclasses import dataclass
from data.classes.aanvragen import Aanvraag
from data.classes.action_log import ActionLog
from data.classes.bedrijven import Bedrijf
from data.classes.files import File, Files
from data.classes.milestones import Milestone
from data.classes.studenten import Student
from data.classes.verslagen import Verslag

DBtype = str|int|float

@dataclass
class DetailRec:
    main_key: int 
    detail_key: int
DetailRecs = list[DetailRec]

AAPAClass = Bedrijf|Student|File|Files|Aanvraag|ActionLog|Verslag|Milestone|DetailRec
KeyClass = int|str
