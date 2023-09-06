from __future__ import annotations

import tkinter.filedialog as tkifd
import datetime
from enum import Enum, auto
from rich.text import Text
from typing import Iterable, Protocol
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, RichLog, Static
from textual.message import Message
import logging

from tui.common.button_bar import ButtonBar, ButtonDef
from general.singleton import Singleton

class TerminalWrite(Message):
    class Level(Enum):
        NORMAL = auto()
        WARNING = auto()
        ERROR  = auto()
    def __init__(self, line: str, write_class: Level = Level.NORMAL, no_newline=False) -> None:
        self.line = line
        self.write_class = write_class
        self.no_newline = no_newline
        super().__init__()
class RunScript(Protocol):
    def __call__(self, **kwdargs)->bool:
        pass

class TerminalForm(Static):
    def compose(self)->ComposeResult:
        yield RichLog()
        yield ButtonBar([ButtonDef('Save Log', variant= 'primary', id='save_log'),
                         ButtonDef('Close', variant ='success', id='close')])
    @property
    def terminal(self)->RichLog:
        return self.query_one(RichLog)

class TerminalScreen(Screen):
    DEFAULT_CSS = """
        TerminalScreen {
            align: center middle;
            background: black 50%;
        }
        TerminalForm {
            width: 90%;
            height: 90%;
        }
        TerminalForm RichLog {
            background: black;
            color: lime;
            border: round white;      
            min-height: 20;
            min-width: 80; 
        }
        TerminalScreen ButtonBar Button {
            max-width: 20;
            outline: solid yellowgreen;
        }
    """
    def __init__(self, **kwdargs):
        self._running = False
        self._error_color = 'red1'
        self._warning_color = 'dark_orange'
        super().__init__(**kwdargs)
    def compose(self) -> ComposeResult:
        yield TerminalForm()
    @property
    def terminal(self)->RichLog:
        return self.query_one(TerminalForm).terminal
    def __script_wrapper(self, script: RunScript, **kwdargs):
        result = script(**kwdargs)
        self.post_message(TerminalWrite(f'READY {result}  {datetime.datetime.strftime(datetime.datetime.now(), "%d-%m-%Y, %H:%M:%S")}'))
    @work(exclusive=True, thread=True)
    async def run(self, script: RunScript, **kwdargs)->bool:
        try:
            self._running = True
            self.__script_wrapper(script, **kwdargs)
        finally:
            self._running = False
    def clear(self):
        self.terminal.clear()
    def write(self, s: str):
        self.terminal.write(s)
    def write_line(self, s: str):
        self.terminal.write(s)
    def write_lines(self, lines:Iterable[str]):
        for line in lines:
            self.terminal.write_line(line)
    def warning(self, message: str, warning_str= 'WARNING'):
        self.write_line(Text(f'{warning_str}: {message}', self._warning_color))
    def error(self, message: str, error_str= 'ERROR'):
        self.write_line(Text(f'{error_str}: {message}', self._error_color))
    def close(self):
        if not self._running:
            self.dismiss(True)
    def save_log(self, filename: str):
        with open(filename, 'w') as file:
            for line in self.terminal.lines:
                file.write(line.text +'\n')
    def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case 'save_log': 
                if (filename:=tkifd.asksaveasfilename(title='Save to file', defaultextension='.log')):
                    self.save_log(filename)
            case 'close': self.close()
            # case 'cancel': dit werkt niet echt, want de thread loopt gewoon door al wordt het "gecanceld"...
            #     self.write_line('cancelling')
            #     cancelled = self.workers.cancel_group(self, 'default')
            #     self.write_line(str(cancelled))
        message.stop()
    async def on_terminal_write(self, msg: TerminalWrite):
        match msg.write_class:
            case TerminalWrite.Level.NORMAL: 
                if msg.no_newline:
                    self.write(msg.line)
                else:
                    self.write_line(msg.line)
            case TerminalWrite.Level.WARNING: self.warning(msg.line)
            case TerminalWrite.Level.ERROR: self.error(msg.line)

class Console(Singleton):
    def __init__(self, app: App, name='terminal'):
        self._app: App = app
        self._app.install_screen(TerminalScreen(), name=name)
        self._name = name
        self._terminal: TerminalScreen = self._app.get_screen(name)
        self._run_result = None
        self._active = False
    def callback_run_terminal(self, result: bool):
        self._run_result = result
        self._active = False    
    async def show(self)->bool:
        if self._active:
            return
        await self._app.push_screen(self._name, self.callback_run_terminal)
        self._active = True
        self._run_result = None
        self._terminal.clear()
    def print(self, msg: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(msg))
    def warning(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.WARNING))
    def error(self, message: str):
        if self._active:
            self._terminal.post_message(TerminalWrite(message, TerminalWrite.Level.ERROR))

_global_console: Console = None
async def init_console(app: App)->Console:
    global _global_console
    if _global_console is None:
        _global_console = Console(app)
    return _global_console

def console_print(msg: str):
    global _global_console
    if _global_console:
        _global_console.print(msg)

def console_warning(msg: str):
    global _global_console
    if _global_console:
        _global_console.warning(msg)

def console_error(msg: str):
    global _global_console
    if _global_console:
        _global_console.error(msg)

async def console_run(script, **kwdargs)->bool:
    global _global_console
    if _global_console:
        return _global_console._terminal.run(script, **kwdargs)
    
async def show_console()->bool:
    global _global_console
    if _global_console:
        await _global_console.show()
        return True
    return False

if __name__=="__main__":
    from textual.widgets import Header, Footer
    from textual.app import App

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
