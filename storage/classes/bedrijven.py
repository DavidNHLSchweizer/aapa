from database.aapa_database import BedrijfTableDefinition
from data.classes.bedrijven import Bedrijf
from storage.general.CRUDs import register_crud

register_crud(class_type=Bedrijf, 
                table=BedrijfTableDefinition()
                )