""" M_TEST """
from types import ModuleType
from migrate.migration_plugin import MigrationPlugin
from process.aapa_processor.aapa_processor import AAPARunnerContext

class TextMigra(MigrationPlugin):
    def process(self, context: AAPARunnerContext, **kwdargs)->bool:
        print('Hello Migration')