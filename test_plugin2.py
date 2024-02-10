from plugins.plugin import PluginBase

class TestPlugin2(PluginBase):
    def run(self, args: list[str]=None):
        result = super().run(args)
        print(f'hello test2 {result}')
        return result
