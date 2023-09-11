from __future__ import annotations
import tkinter.filedialog as tkifd
from enum import Enum, auto
from rich.text import Text
from typing import Iterable, Protocol
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, RichLog, Static
from textual.message import Message
from tui.common.button_bar import ButtonBar, ButtonDef

class TerminalWrite(Message):
    class Level(Enum):
        NORMAL  = auto()
        INFO    = auto()
        WARNING = auto()
        ERROR   = auto()
    def __init__(self, line: str, write_class: Level = Level.NORMAL, no_newline=False) -> None:
        self.line = line
        self.write_class = write_class
        self.no_newline = no_newline
        super().__init__()
class RunScript(Protocol):
    def __call__(self, **kwdargs)->bool:
        pass

ToolTips = {'save_log':'Schrijf de AAPA-uitvoer naar een tekstbestand', 
            'close': 'Sluit dit venster',
            }
class TerminalForm(Static):
    def compose(self)->ComposeResult:
        yield RichLog()
        yield ButtonBar([ButtonDef('Save Log', variant= 'primary', id='save_log'),
                         ButtonDef('Close', variant ='success', id='close')])
    @property
    def terminal(self)->RichLog:
        return self.query_one(RichLog)
    def on_mount(self):
        for id in {'save_log', 'close'}:
            self.query_one(f'#{id}', Button).tooltip = ToolTips[id]


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
        self._info_color = 'white'
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
            self.write_line(line)
    def info(self, message: str):
        self.write_line(Text(message, self._info_color))
    def warning(self, message: str):
        self.write_line(Text(message, self._warning_color))
    def error(self, message: str):
        self.write_line(Text(message, self._error_color))
    def close(self):
        if not self._running:
            self.dismiss(True)
    def save_log(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as file:
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
    async def on_terminal_write(self, message: TerminalWrite):
        match message.write_class:
            case TerminalWrite.Level.NORMAL: 
                if message.no_newline:
                    self.write(message.line)
                else:
                    self.write_line(message.line)
            case TerminalWrite.Level.INFO: self.info(message.line)
            case TerminalWrite.Level.WARNING: self.warning(message.line)
            case TerminalWrite.Level.ERROR: self.error(message.line)
