""" MAKE_AANVRAGEN

    Maakt een aantal aanvragen aan voor specifieke studenten. Reden: deze aanvragen zaten nog niet in de database.
    Omdat de studenten nog niet afgestudeerd zijn worden deze verslagen met terugwerkende kracht gegenereerd. 
    De database wordt daarmee "completer" en bepaalde problemen worden voorkomen.

    De code is bedoeld voor de migratie naar database versie 1.22

"""
import datetime
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.general.const import AanvraagStatus, MijlpaalBeoordeling
from main.log import log_print
from general.timeutil import TSC
from general.sql_coll import SQLcollector, SQLcollectors
from migrate.migration_plugin import MigrationPlugin
from process.main.aapa_processor import AAPARunnerContext

class AanvragenFabricator(MigrationPlugin):
    def init_SQLcollectors(self) -> SQLcollectors:
        sql = super().init_SQLcollectors()
        sql = SQLcollectors()
        sql.add('aanvragen', 
                      SQLcollector({'insert': {'sql':'insert into AANVRAGEN(id,datum,stud_id,bedrijf_id,titel,kans,status,beoordeling,datum_str,versie) values(?,?,?,?,?,?,?,?,?,?)'}}))
        sql.add('bedrijven', 
                      SQLcollector({'insert': {'sql':'insert into BEDRIJVEN(id,name) values(?,?)'}}))
        return sql
    def create_aanvraag(self,student_id: int, bedrijf_name: str, titel: str, datum: datetime.datetime):
        student = self.storage.crud('studenten').read(student_id)
        if (rows:=self.storage.queries('bedrijven').find_values('name', bedrijf_name)):
            bedrijf = rows[0]
        else:
            bedrijf = Bedrijf(bedrijf_name)       
            self.storage.queries('bedrijven').ensure_key(bedrijf)
            self.storage.crud('bedrijven').create(bedrijf)
            self.sql.insert('bedrijven', [bedrijf.id,bedrijf.name])
        aanvraag = Aanvraag(student=student, bedrijf=bedrijf, titel=titel,datum=datum, 
                            beoordeling=MijlpaalBeoordeling.VOLDOENDE,
                            status=AanvraagStatus.READY_IMPORTED,kans=1,versie=1)
        self.storage.crud('aanvragen').create(aanvraag)
        self.sql.insert('aanvragen', [aanvraag.id,TSC.timestamp_to_sortable_str(aanvraag.datum),aanvraag.student.id,aanvraag.bedrijf.id,aanvraag.titel,aanvraag.kans,
                                       aanvraag.status,aanvraag.beoordeling,aanvraag.datum_str,aanvraag.versie])
        log_print(aanvraag)

    aanvraag_data = [
    {'id': 102,'bedrijf': 'Snakeware', 'titel':'Event orchestrating binnen digitale landschap',
        'datum':TSC.str_to_timestamp('26-10-2020 08:39:00')}, #Daan Eekhof
    {'id': 144,'bedrijf': 'Strukton Worksphere', 'titel':'Project Processimulatie',
        'datum':TSC.str_to_timestamp('10-11-2020 09:53:00')}, #Daniel Roskam   
    {'id': 118,'bedrijf': 'Snakeware', 'titel':'Het bouwen van een content managmentsysteem',
        'datum':TSC.str_to_timestamp('01-3-2022 06:04:00')}, #Jasper de Jong  
    {'id': 122,'bedrijf': 'Beenen', 'titel':'Automatiseren van logistieke handelingen', 
        'datum':TSC.str_to_timestamp('12-4-2022 09:36:00')}, #Michael Koopmans  
    {'id': 95, 'bedrijf': 'CJIB', 'titel':'Generieke geautomatiseerde testrapportage',
        'datum':TSC.str_to_timestamp('10-10-2022 09:12:00')}, #Micky Cheng
    {'id': 172,'bedrijf': 'Kwant Controls', 'titel':'CAESAR configurator',
        'datum':TSC.str_to_timestamp('27-6-2022 13:58:00')}, #Nick Westerdijk 
    {'id': 84, 'bedrijf': 'Enpron / Controol', 'titel':'BOUWEN VAN EEN VOORSPELLEND MODEL VOOR ENERGIEOPWEKKING',
        'datum':TSC.str_to_timestamp('28-4-2022 14:28:00')}, #Sander Beijaard 
    ]  

    def process(self, context: AAPARunnerContext, **kwdargs)->bool:  
        for entry in self.aanvraag_data:
            self.create_aanvraag(entry['id'], entry['bedrijf'], entry['titel'], entry['datum'])
        return True

