import logging
from typing import Iterable

from textual.app import ComposeResult
from textual.message_pump import MessagePump
from textual.containers import Center
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.message import Message

from button_bar import ButtonBar, ButtonDef
            
def get_split_width(s: str)->int:
    return max(len(substr) for substr in s.split('\n'))

class DialogMessage(Message):
    def __init__(self, result_str: str, originator_key: str):
        self.result_str = result_str
        self.originator_key = originator_key
        super().__init__()

class DialogForm(Static):
    DEFAULT_CSS = """   
        DialogForm {
            align: center middle;
            height: 11;
            border: thick $surface 50%;
            background: wheat;
        }
        DialogForm Label{
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
            color: black;
        }
    """    
    def __init__(self, label_str: str, buttons: Iterable[ButtonDef]): 
        self._label_str = label_str
        self._buttons = buttons
        super().__init__()
    def compose(self) -> ComposeResult:
        with Center():
            yield Label(self._label_str)
            yield ButtonBar(self._buttons)
    def on_mount(self):
        w = 2 + max(self.__total_button_width(), self.__label_width())
        bw = self.__button_width()
        logging.debug(f'label: {self.__label_width()} button: {bw} totalbuttons: {self.__total_button_width()} -> {w=}')
        self.styles.min_width = w
        self.styles.width = w
        for button in self.query(Button):
            button.styles.width = bw
    def __total_button_width(self)->int:
        return len(self._buttons) * (self.__button_width() + 2) + 4
    def __button_width(self)->int:
        return max(12, max(len(button.label) for button in self._buttons)) + 6
    def __label_width(self)->int:
        return get_split_width(self._label_str) + 4

class DialogScreen(ModalScreen[str]):
    DEFAULT_CSS = """   
        DialogScreen {
            align: center middle;
            background: wheat 50%;
        }
        DialogScreen DialogForm{
            align: center middle;
            max-width: 120;
            height: 11;
            border: thick $surface 50%;
        }
    """
    def __init__(self, label_str: str, buttons: Iterable[ButtonDef], originator_key: str):
        self._label_str = label_str
        self._buttons = buttons
        self.originator_key = originator_key
        self.dialog_result  = None
        super().__init__()
    def compose(self) -> ComposeResult:
        yield DialogForm(self._label_str, self._buttons)
    def run(self, originator: MessagePump)->str:
        def __callback_verify(result: str):
            originator.post_message(DialogMessage(result, self.originator_key))
        self.dialog_result  = None
        self.app.push_screen(self, callback = __callback_verify)                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.label)
        event.stop()

def run_dialog(originator: MessagePump, screen: DialogScreen)->str:
    return screen.run(originator)

def message_box(originator: MessagePump, message: str, originator_key='message'):
    run_dialog(originator, DialogScreen(message, [ButtonDef('OK', variant='primary')], originator_key=originator_key))
               
def verify(originator: MessagePump, question: str, originator_key='verify', buttons=['Ja', 'Nee'])->str:
    return run_dialog(originator, DialogScreen(question, [ButtonDef(buttons[0], variant='success'), ButtonDef(buttons[1], variant='error')], originator_key=originator_key))
def verify_cancel(originator: MessagePump, question: str, originator_key='verify_cancel', buttons=['Ja', 'Nee', 'Afbreken'])->str:
    return run_dialog(originator, DialogScreen(question, [ButtonDef(buttons[0], variant='success'), ButtonDef(buttons[1], variant='primary'), ButtonDef(buttons[2], variant='error')], 
                                               originator_key=originator_key))

if __name__ == "__main__":
    from textual.widgets import Header, Footer
    from textual.app import App

    logging.basicConfig(filename='verify.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    class TestApp(App):
        BINDINGS = [("v", "verify", "Verify"), ("c","verify_cancel", 'verify with cancel'), ("o", "verifyOK", "Verify with OK"), ]
        
        def compose(self) -> ComposeResult:
            yield Header()
            yield Footer()
    
        async def action_verify(self) -> None:
            """An action to test verify."""
            result = verify(self, 'Wat is daarop uw antwoord? Wat is daarop uw antwoord? Wat is \ndaarop uw antwoord? Wat is daarop uw antwoord? ')
            logging.debug(f'returned: {result}')            

        async def action_verifyOK(self) -> None:
            """An action to test verify."""
            result = verify(self, 'Wat is daarop uw antwoord?', buttons = ['OK','Cancel'], originator_key='OKC')
            logging.debug(f'returned: {result}')            

        async def action_verify_cancel(self) -> None:
            """An action to test verify."""
            result = verify_cancel(self, 'Wat is daarop uw antwoord?')
            logging.debug(f'returned: {result}')            

        def on_dialog_message(self, event: DialogMessage):
            logging.debug(f'resultaat: {event.result_str} {event.originator_key}')
            match event.originator_key:
                case 'verify':
                    message_box(self, f'Het antwoord is resultaat: {event.result_str} {event.originator_key}')
                case 'verify_cancel':
                    message_box(self, f'Het antwoord is met cancel\nresultaat: {event.result_str} {event.originator_key}')
                case 'OKC':
                    message_box(self, f'Het antwoord is resultaat: {event.result_str} {event.originator_key}')

    app = TestApp()
    app.run()