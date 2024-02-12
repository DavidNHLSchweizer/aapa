import logging
from textual.app import App
from textual.screen import ScreenResultCallbackType
from main.log import ConsoleFactory, PrintFuncs
from general.singleton import Singleton
from tui.general.terminal import TerminalScreen, TerminalWrite

class Console(Singleton):
    def __init__(self, app: App, callback: ScreenResultCallbackType = None, name='terminal'):
        self._app: App = app
        self._app.install_screen(TerminalScreen(), name=name)
        self._name = name
        self._terminal: TerminalScreen = self._app.get_screen(name)
        self._run_result = None
        self._active = False
        self._callback = callback
    def callback_run_terminal(self, result: bool):
        self._run_result = result
        self._active = False    
        if self._callback:
            self._callback(result)
    async def show(self)->bool:
        if self._active:
            return
        await self._app.push_screen(self._name, self.callback_run_terminal)
        self._active = True
        self._run_result = None
        self._terminal.clear()
    def print(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message))
    def info(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.INFO))
    def warning(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.WARNING))
    def error(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.ERROR))
    def debug(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.DEBUG))

_global_console: Console = None
async def init_console(app: App, callback: ScreenResultCallbackType)->Console:
    global _global_console
    if _global_console is None:
        _global_console = Console(app, callback=callback)
    return _global_console

def console_print(message: str):
    global _global_console
    if _global_console:
        _global_console.print(message)

def console_info(message: str):
    global _global_console
    if _global_console:
        _global_console.info(message)

def console_warning(message: str):
    global _global_console
    if _global_console:
        _global_console.warning(message)

def console_error(message: str):
    global _global_console
    if _global_console:
        _global_console.error(message)

def console_debug(message: str):
    global _global_console
    if _global_console:
        _global_console.debug(message)

class TerminalConsoleFactory(ConsoleFactory):
    def create(self)->PrintFuncs:
        return PrintFuncs(console_print, console_info, console_warning, console_error, console_debug)


async def console_run(script, **kwdargs)->bool:
    global _global_console
    if _global_console:
        return await _global_console._terminal.run(script, **kwdargs)
    
async def show_console()->bool:
    global _global_console
    if _global_console:
        await _global_console.show()
        return True
    return False

if __name__=="__main__":
    from textual.widgets import Header, Footer
    from textual.app import App, ComposeResult
    from datetime import datetime

    def testscript(**kwdargs)->bool:
        console_print(f'params {kwdargs}')
        for i in range(1,kwdargs.pop('N')):
            if i % 1600 == 0:
                console_warning(f'nu is i = {i}\n maar niet heus...')
            if i % 2000 == 0:
                console_error(f'nu is i = {i}'.upper())
            if i % 300 == 0:
                console_print(f'dit is {i}')            
        return False

    class TestApp(App):
        BINDINGS= [('r', 'run', 'Run terminal')]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Footer()
        async def on_mount(self):
            await init_console(self)
        async def action_run(self):
            if await show_console():
                console_print(f'INITIALIZE RUN {datetime.datetime.strftime(datetime.datetime.now(), "%d-%m-%Y, %H:%M:%S")}')
                await console_run(testscript, N=95000)

if __name__ == "__main__":
    logging.basicConfig(filename='terminal.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    app = TestApp()
    app.run()
