from textual.app import ComposeResult
from textual.css.scalar import Scalar, Unit
from textual.widgets import Collapsible, Label, Static, Switch
from textual.containers import Horizontal, Vertical

class LabeledSwitch(Static):
    DEFAULT_CSS = """
    LabeledSwitch {
        height: 2;
        align: left middle;
        border: none;
    }
    .label {
        margin: 1 0 0 1;
        padding: 0 0 0 1;
        color: black;
    } 
    .switch {
        border: none;
        margin: 1 5 0 0;
        min-width: 5;
        align: right middle;
    }
    .switch:focus{
         border: none; 
         background: white;  
    }
    .switch:hover{
        border: none;   
    }
    
    """
    def __init__(self, label: str, width=None, **kwdargs):
        self._width = width
        self._label = label
        super().__init__(**kwdargs)
    def compose(self)->ComposeResult:
        with Horizontal():
            yield Label(self._label, id=self._label_id(), classes='label')
            yield Switch(value=True, id=self._switch_id(), classes='switch')
    def _label_id(self)->str:
        return f'{self.id}-label'
    def _switch_id(self)->str:
        return f'{self.id}-switch'
    def on_mount(self):
        if self._width:
            self.styles.width = Scalar(self._width, Unit.CELLS, Unit.WIDTH)
        else:
            self.styles.width = Scalar(100, Unit.WIDTH, Unit.PERCENT)
    @property
    def value(self)->bool:
        return self.query_one(Switch).value    
    @value.setter
    def value(self,value: bool):
        self.query_one(Switch).value = value

class LabeledSwitchGroup(Static):
    DEFAULT_CSS = """
    LabeledSwitchGroup {
        border: round purple;
        background: wheat;
    }
    """
    def __init__(self, labels: list[str], width = None, title='', **kwdargs):
        self._width = width
        self._labels = labels
        super().__init__(**kwdargs)
        self.border_title = title
    def compose(self)->ComposeResult:
        maxlen = max([len(label) for label in self._labels]) 
        with Vertical():
            for label in self._labels:
                yield LabeledSwitch(label.rjust(maxlen))
    def on_mount(self):
        self.styles.max_height = len(self._labels) * 2 + 2
        self.styles.min_height = self.styles.max_height
        if self._width:
            self.styles.width = Scalar(self._width, Unit.CELLS, Unit.WIDTH)
        else:
            self.styles.width = Scalar(100, Unit.WIDTH, Unit.PERCENT)
    @property
    def _switches(self)->list[LabeledSwitch]:
        return self.query(LabeledSwitch)
    def get_value(self, index: int)->bool:
        return self._switches[index]
    def set_value(self, index: int, value: bool):
        self._switches[index].value = value
         
if __name__ == "__main__":
    import logging
    from textual.app import App
    from textual.widgets import Footer
    class TestApp(App):
        BINDINGS = [
                    ('t', 'toggle_', 'Toggle switches'),
                    ]  
        def compose(self) -> ComposeResult:
            # with Collapsible(title='Input options'):
            yield LabeledSwitchGroup(width=42,  
                                     labels=['MS-Forms Excel file:', 'PDF-files (directory scan):', 'Blackboard ZIP-files:'], id ='lsg')
            yield(Footer())
        def action_toggle_(self):           
            for labi in self.query(LabeledSwitch):
                labi.value = not labi.value

    logging.basicConfig(filename='testing.log', filemode='w', format='%(module)s-%(funcName)s-%(lineno)d: %(message)s', level=logging.DEBUG)
    app = TestApp()
    app.run()        