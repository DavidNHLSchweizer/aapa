from textual.app import ComposeResult
from textual.css.scalar import Scalar, Unit
from textual.widgets import Static, Label, Input, Button, Switch
from textual.containers import Horizontal
from textual.events import Resize
import logging

from tui.general.utils import id2selector

class InputWithButton(Static):
    DEFAULT_CSS = """
    InputWithButton {
        height: 3;
        layout: horizontal;
    }
    .small {
        max-width: 5;
        min-width: 5;
    }
    """
    def __init__(self, width=None, **kwdargs):
        self._width = width
        self._validators = kwdargs.pop('validators', None)
        super().__init__(**kwdargs)
    def compose(self)->ComposeResult:
        yield Input(id=self._input_id(), validators=self._validators)
        yield Button('...', id=self._button_id(), classes='small')
    def _input_id(self)->str:
        return f'{self.id}-input'
    def _button_id(self)->str:
        return f'{self.id}-button'
    def on_mount(self):
        if self._width:
            self.styles.width = Scalar(self._width, Unit.CELLS, Unit.WIDTH)
        else:
            self.styles.width = Scalar(100, Unit.WIDTH, Unit.PERCENT)
    @property
    def _button_size(self)->int:
        return 5
    def on_resize(self, message: Resize):        
        self.input.styles.width = message.size.width - self._button_size
    @property
    def input(self)->Input:
        return self.query_one(Input)
    @property
    def button(self)->Button:
        return self.query_one(Button)
    @property
    def value(self)->str:
        return self.input.value
    @value.setter
    def value(self, value: str):
        self.input.value = value

class LabeledInput(Static):
    HORIZONTAL = 'labeled_input--horizontal'
    VERTICAL   = 'labeled_input--vertical'
    COMPONENT_CLASSES = [HORIZONTAL, VERTICAL]

    DEFAULT_CSS = """
    LabeledInput{
        max-height: 4;
    }
    LabeledInput.labeled_input--horizontal {
        layout: horizontal;
    }
    LabeledInput.labeled_input--horizontal Label {
        align-vertical: middle;
        margin: 1 1 0 0;
    }
    LabeledInput.labeled_input--horizontal Input {
        max-width: 100%;
    }
    LabeledInput.labeled_input--vertical {
        layout: vertical;
        align-horizontal: left;
        margin: 0 0 0 0;
        width: 100%;
        max-width: 100%;
    }
    LabeledInput Switch {
        width: 8;
        border: none;
        margin: 0 2 0 1;
        min-width: 5;
        align: left middle;
        height: 1;
    }
    .switch {
        border: none;
        min-width: 5;
        align: right middle;
    }
    .switch:focus{
         border: none; 
         background: sandybrown;  
    }
    .switch:hover{
        border: none;   
    }

    """
    def __init__(self, label_text, horizontal=False, width=None, button=False, switch=False, **kwdargs):
        self._label_text = label_text
        self._width = width
        self._validators = kwdargs.pop('validators', None)
        self._button = button
        self._switch = switch
        self._switch_width = 11 if self._switch else 0
        super().__init__('', **kwdargs, classes = LabeledInput.HORIZONTAL if horizontal else LabeledInput.VERTICAL)
    def compose(self)->ComposeResult:
        if self._switch:
            with Horizontal():
                yield Switch(True, id = self._switch_id(),classes='switch')
                yield Label(self._label_text, id=self._label_id())
        else:
            yield Label(self._label_text, id=self._label_id())
        if self._button:
            yield InputWithButton(id=self._input_id(), validators=self._validators, width=self._width)
        else:
            yield Input('', id=self._input_id(), validators=self._validators) 
    def on_mount(self):
        if self._width:
            self.styles.width = Scalar(self._width, Unit.CELLS, Unit.WIDTH)
        else:
            self.styles.width = Scalar(100, Unit.WIDTH, Unit.PERCENT)
        if self._switch:
            switch = self.query_one(id2selector(self._switch_id()))
            self.post_message(Switch.Changed(switch,switch.value))
    def _label_id(self)->str:
        return f'{self.id}-label'
    def _input_id(self)->str:
        return f'{self.id}-input'
    def _switch_id(self)->str:
        return f'{self.id}-switch'
    def on_switch_changed(self,message: Switch.Changed):
        label = self.query_one(id2selector(self._label_id()))
        input = self.query_one(id2selector(self._input_id()))
        if message.value:
            label.styles.color = 'black'
            input.styles.color = 'black'
            input.styles.text_style = 'none'
            input.disabled = False
        else:
            label.styles.color = 'gray'
            input.styles.text_style = 'italic'
            input.disabled = True
    
    @property
    def input(self)->Input:
        return self.query_one(id2selector(self._input_id()), Input)
    def on_resize(self, message: Resize):        
        if self.horizontal:            
            self.input.styles.width = message.size.width - len(self._label_text)-1 - self._switch_width
        else:
            self.input.styles.width = message.size.width - self._switch_width
    @property
    def input(self)->Input | InputWithButton:
        return self.query_one(id2selector(self._input_id()))
    @property
    def switch(self)->Switch:
        return self.query_one(id2selector(self._switch_id())) if self._switch else None
    @property
    def value(self)->str:
        return self.input.value
    @value.setter
    def value(self, value: str):
        self.input.value = value
    @property
    def switch_value(self)->str:
        return self.switch.value
    @switch_value.setter
    def switch_value(self, value: str):
        self.switch.value = value
    @property
    def label(self)->Label:
        return self.query_one(id2selector(self._label_id()), Label)
    @property
    def horizontal(self)->bool:
        return LabeledInput.HORIZONTAL in self.classes 
    @horizontal.setter
    def horizontal(self, value: bool):
        self.classes = LabeledInput.HORIZONTAL if value else LabeledInput.VERTICAL

if __name__ == "__main__":
    import logging
    from textual.app import App
    from textual.widgets import Footer
    from utils import Required
    class TestApp(App):
        BINDINGS = [
                    ('t', 'toggle_', 'Toggle horizontal'),
                    ]  
        def compose(self) -> ComposeResult:
            yield InputWithButton(width=80, validators=Required())
            yield LabeledInput('Labeling', False, width=100, validators=Required(), switch=True, id='labeling')
            yield LabeledInput('Two Labeling', True, width=100, validators=Required(), switch=True, id='labeling2')
            yield LabeledInput('qbux234234 234234 234 234', False, width=50, validators=None, id='labeling2bbb')
            yield LabeledInput('Raveling', True, width=80, button=True, switch=True, validators=Required(), id='labeling3')
            yield LabeledInput('qbux234234 dsriugt6i3u4ui 234', False, switch=True, width=90, button=True, validators=None, id='labeling4')
            yield LabeledInput('Sexy mf', False, validators=Required(), switch=True, button=True, id='labeling5')
            yield LabeledInput('TRaveling Light', True, validators=Required(), switch=True, button=True, id='labeling7')
            yield Button('De Button')
            yield Footer()
        def action_toggle_(self):           
            for labi in self.query(LabeledInput):
                labi.horizontal = not labi.horizontal

    logging.basicConfig(filename='testing.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    app = TestApp()
    app.run()