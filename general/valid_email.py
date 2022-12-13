import re

class EmailValidator:
    def __init__(self):
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        nhlstenden_email_regex = r'[A-Za-z0-9._%+-]+@student.nhlstenden.com'
        self.pattern = re.compile(email_regex)
        self.nhlstenden = re.compile(nhlstenden_email_regex)
    def is_valid_email(self, email: str)->bool:
        return self.pattern.fullmatch(email) is not None 
    def try_extract_nhlstenden_email(self, email: str)->str:
        if (m:= self.nhlstenden.search(email)):
            return email[m.start():m.end()]
        return self.try_extract_email(email)
    def try_extract_email(self, email: str)->str:
        if (m:= self.pattern.match(email)):
            return email[m.start():m.end()]
        return None

def is_valid_email(email: str)->bool:
    return EmailValidator().is_valid_email(email)

def try_extract_email(email: str, nhlstenden = False)->str:
    if nhlstenden:
        return EmailValidator().try_extract_nhlstenden_email(email)
    else:
        return EmailValidator().try_extract_email(email)

if __name__=='__main__':        
    f = r'steenhuisjasper1@gmail.com / jasper.steenhuis@student.nhlstenden.com'
    g = r'jasper.steenhuis@student.nhlstenden.com'
    print(f'f: {f} :  {try_extract_email(f, True)}')
    print(f'g: {g} :  {try_extract_email(g, True)}')
    