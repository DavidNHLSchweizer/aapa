from dataclasses import dataclass
from typing import Iterable
from textual.app import ComposeResult
from textual.widgets import Button, Static

@dataclass
class ButtonDef:
    label: str = None
    variant: str = 'default'
    name: str = None
    id: str = None
    classes: str = None
    disabled: bool = False

class ButtonBar(Static):
    DEFAULT_CSS = """   
        ButtonBar{
            align: center middle;
        }
        ButtonBar.horizontal {
            layout: horizontal;
        }
        ButtonBar.vertical {
            layout: vertical;
        }
    	ButtonBar.horizontal Button {
            margin: 0 1 0 1;
        }
    	ButtonBar.vertical Button {
            margin: 1 0 1 0;
        }
    """
    
    def __init__(self, buttons: Iterable[ButtonDef], horizontal=True, **kwdargs):
        self._buttons = buttons
        super().__init__(classes = 'horizontal' if horizontal else 'vertical', **kwdargs)
    def compose(self)->ComposeResult:
        for button in self._buttons:
            yield Button(label=button.label, variant=button.variant, name=button.name, id=button.id, classes=button.classes, disabled=button.disabled)
    def nr_buttons(self)->int:
        return len(self.query(Button))

if __name__== '__main__':
    from textual.widgets import Header, Footer
    from textual.app import App

    import logging
    logging.basicConfig(filename='verify.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    class TestApp(App):
        DEFAULT_CSS = """
        ButtonBar.horizontal {
            outline: round purple;
            background: lightgray;
            min-width: 100;
            height: 5;
        }
        ButtonBar.vertical {
            outline: round green;
            background: rgb(224,33,138);
            width: 30;
        }
        """
        def compose(self) -> ComposeResult:
            yield Header()
            yield ButtonBar([ButtonDef('hallo', variant='primary'), ButtonDef('goodbye', variant='error'), ButtonDef('zwaai', variant='success')])
            yield ButtonBar([ButtonDef('hallo', variant='primary'), ButtonDef('goodbye', variant='error'), ButtonDef('zwaai', variant='success')], horizontal=False)
            yield Footer()
    
    app = TestApp()
    app.run()    