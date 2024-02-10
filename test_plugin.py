from plugins.plugin import PluginBase

class TestPlugin(PluginBase):
    def run(self, args: list[str]=None)->bool:
        if not super().run(args):
            return False
        print(f'hello test')
        return True
