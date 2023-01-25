from dataclasses import dataclass

@dataclass
class FieldSubstitution:
    code: str
    keyword: str

class FieldSubstitutions:
    def __init__(self, substitutions: list[FieldSubstitution]):
        self.substitutions = substitutions
    def translate(self, line: str, **kwdargs)->str:
        for substitution in self.substitutions:
            if substitution.keyword in kwdargs:
                line = line.replace(substitution.code, kwdargs.get(substitution.keyword))
        return line

