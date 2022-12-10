from data.AAPdatabase import BedrijfTableDefinition, FileTableDefinition
from data.aanvraag_info import Bedrijf
from database.crud import CRUDbase
from database.database import Database
from database.sqlexpr import Ops, SQLexpression as SQE

class CRUD_bedrijven(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, BedrijfTableDefinition())
    def __get_create_columns(self):
        return ['name']
    def __get_create_values(self, bedrijf: Bedrijf):
        return [bedrijf.bedrijfsnaam]
    
    def create(self, bedrijf: Bedrijf):
        super().create(columns=self.__get_create_columns(), values=self.__get_create_values(bedrijf))   
    def read(self, id: int)->Bedrijf:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return Bedrijf(row['name'], id)
        else:
            return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=['name'], values=[bedrijf.bedrijfsnaam], where=SQE('id', Ops.EQ, bedrijf.id))
    def delete(self, bedrijf: Bedrijf):
        super().delete(where=SQE('id', Ops.EQ, bedrijf.id))

class CRUD_files(CRUDbase):
    def __init__(self, database: Database):
        super().__init__(database, FileTableDefinition())

    def __get_create_columns(self):
        return ['filename', 'timestamp', 'filetype']
    def __get_create_values(self, file: File):
        return [bedrijf.bedrijfsnaam]
    
    def create(self, bedrijf: Bedrijf):
        super().create(columns=self.__get_create_columns(), values=self.__get_create_values(bedrijf))   
    def read(self, id: int)->Bedrijf:
        if row:=super().read(where=SQE('id', Ops.EQ, id)):
            return Bedrijf(row['name'], id)
        else:
            return None
    def update(self, bedrijf: Bedrijf):
        super().update(columns=['name'], values=[bedrijf.bedrijfsnaam], where=SQE('id', Ops.EQ, bedrijf.id))
    def delete(self, bedrijf: Bedrijf):
        super().delete(where=SQE('id', Ops.EQ, bedrijf.id)

