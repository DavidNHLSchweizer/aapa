from data.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from data.storage.CRUDs import register_crud

register_crud(class_type=Bedrijf, 
                table=BedrijfTableDefinition()
                )