from textual.app import ComposeResult
from textual.widgets import Static, Button, RadioSet, RadioButton
from textual.containers import Horizontal

from tui.const import MISSINGHELP, ToolTips

class RadioSetPanel(Static):
    def __init__(self, values: list[str], **kwdargs):
        self._values = values
        super().__init__(**kwdargs)
    def compose(self)->ComposeResult:
        with RadioSet():
            for n,value in enumerate(self._values):
                yield RadioButton(value, id=value, value=n==0)

class PreviewPanel(RadioSetPanel):
    def __init__(self, **kwdargs):
        super().__init__(values=['preview', 'uitvoeren'], **kwdargs)

class ModePanel(RadioSetPanel):
    def __init__(self, **kwdargs):
        super().__init__(values=['aanvragen', 'rapporten'], **kwdargs)

class AapaProcessingForm(Static):
    DEFAULT_CSS = """
        AapaProcessingForm {
            height: 5;
            background: $background;
            margin: 0;
            border: round purple;
        }
        AapaProcessingForm RadioSetPanel {
            max-width: 38;
            min-width: 38;
            padding: 0 0 0 0;
        }
        AapaProcessingForm RadioSet {
            layout: horizontal;
            outline: solid purple;    
            margin: 0 2 0 2;
        }
        AapaProcessingForm RadioButton {
            color: black; 
        }
    """
    def compose(self)->ComposeResult:
        with Horizontal():
            yield(ModePanel())
            yield(PreviewPanel())
    def on_mount(self):
        self.border_title = 'Verwerking'
        tooltips = ToolTips.get('processing', {})
        for id in {'preview', 'uitvoeren', 'aanvragen', 'rapporten'}:
            self.query_one(f'#{id}').tooltip = tooltips.get(f'mode_{id}', MISSINGHELP) 
    def toggle(self):
        self.preview = not self.preview
    @property
    def preview(self)->bool:
        return self.query_one('#preview', RadioButton).value
    @preview.setter
    def preview(self, value: bool):
        if value: #note: this is the only way it works properly
            self.query_one('#preview', RadioButton).value = True
        else:
            self.query_one('#uitvoeren', RadioButton).value= True
