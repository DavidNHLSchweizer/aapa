from data.general.const import MijlpaalType
from data.classes.files import File
from plugins.plugin import PluginBase
from process.main.aapa_processor import AAPARunnerContext
from tests.random_data import RandomData

class TestPlugin(PluginBase):
    def before_process(self, context: AAPARunnerContext, **kwdargs)->bool:
        self.storage = context.storage
        self.database = self.storage.database
        return True

    def test_aanvragen(self, RD: RandomData):
        aanvraag = self.storage.read('aanvragen', 100)
        print(aanvraag)
        for file in aanvraag.files.files:
            print(File.display_file(file.filename))
        a = RD.random_aanvraag()
        print(a)
        for file in a.files.files:
            print(File.display_file(file.filename))
        self.storage.create('aanvragen', a)
        print(f'----- aanvraag: {a.id}')
        a1 = self.storage.read('aanvragen', a.id)
        print(f'na create: {a1=}')
        for file in a1.files.files:
            print(File.display_file(file.filename))
        a.titel = 'zuip schuit'
        a.files.add(RD.random_file(File.Type.GRADE_FORM_DOCX, MijlpaalType.AANVRAAG))
        self.storage.update('aanvragen', a)
        b = self.storage.read('aanvragen',  a.id)
        print(b)
        for file in b.files.files:
            print(File.display_file(file.filename))
        self.storage.delete('aanvragen', b)
        c = self.storage.read('aanvragen',  a.id)
        print(c)
    def test_undologs(self, RD: RandomData):
        undo=self.storage.read('undo_logs', 60)
        print(undo)
        for file in undo.files:
            print(File.display_file(file.filename))
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        RD = RandomData(self.storage)
        self.test_aanvragen(RD)
        self.test_undologs(RD)
        self.database.commit()
        return True
    