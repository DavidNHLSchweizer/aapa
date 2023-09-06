from textual.validation import Function

class Required(Function):
    def __init__(self):
        super().__init__(function = lambda value: len(value) > 0)