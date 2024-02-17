from textual.validation import Function

def id2selector(id: str)->str:
    return f'#{id}'

class Required(Function):
    def __init__(self):
        super().__init__(function = lambda value: len(value) > 0)
