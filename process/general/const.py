from __future__ import annotations
from enum import Enum, auto


class AAPAaction(Enum):
    """ Acties om uit te voeren.

    NONE: geen actie.
    INPUT: Verwerk input. 
        Voor aanvragen: importeer nieuwe aanvragen. 
        Voor verslagen: importeer nieuwe verslagen.
        Welke hiervan wordt uitgevoerd wordt bepaald door de processing_mode.
        Zie AAPAProcessingOptions.PROCESSINGMODE voor meer info.
    FORM: Maak nieuwe beoordelingsformulieren.
        Ook dit kan worden gedaan voor aanvragen en/of verslagen,
        afhankelijk van de processing_mode.
    MAIL: Lees beoordelingen en zet concept-mails klaar.
    FULL: combinatie van INPUT,FORM en MAIL.
    NEW: maak een nieuwe database aan. Indien de database al bestaat: maak de database leeg.
    INFO: druk de configuratie-informatie af op de console.
    REPORT: maak een aanvragen-rapportage (Aanvragen.XLSX).
    UNDO: maak de vorige actie ongedaan. 

    """
    NONE      = 0
    INPUT     = auto()
    FORM      = auto()
    MAIL      = auto()
    FULL      = auto()
    NEW       = auto()
    INFO      = auto()
    REPORT    = auto()
    UNDO      = auto()
    def help_str(self):
        match self:
            case AAPAaction.NONE: return 'Geen actie [DEFAULT]'
            case AAPAaction.INPUT: return 'Vind en importeer nieuwe aanvragen of verslagen (zie ook --input_options, --processing_mode)'
            case AAPAaction.FORM: return 'Maak beoordelingsformulieren'
            case AAPAaction.MAIL: return 'Vind en verwerk beoordeelde aanvragen en zet feedbackmails klaar'
            case AAPAaction.FULL: return 'Volledig proces: scan + form + mail'
            case AAPAaction.NEW: return 'Maak een nieuwe database of verwijder alle data uit de database (als deze reeds bestaat).'
            case AAPAaction.INFO: return 'Laat configuratie (directories en database) zien'
            case AAPAaction.REPORT: return 'Rapporteer alle aanvragen in een .XLSX-bestand'
            case AAPAaction.UNDO: return 'Ongedaan maken van de laatste procesgang'
            case _: return ''
    @staticmethod
    def all_help_str():
        return '\n'.join([f'   {str(a)}: {a.help_str()}' for a in AAPAaction]) + \
                f'\nDefault is {str(AAPAaction.NONE)}.'
    def __str__(self):    
        return self.name.lower()
    @staticmethod
    def get_choices():
        return [str(a) for a in AAPAaction]
    @staticmethod
    def get_actions_str(actions: list[AAPAaction]):
        return '+'.join([str(a) for a in actions])
    @staticmethod
    def from_action_choice(action_choice: str)->AAPAaction:
        for a in AAPAaction:
            if str(a) == action_choice:
                return a
        return None

