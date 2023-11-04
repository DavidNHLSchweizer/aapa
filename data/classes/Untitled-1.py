class tttt:
    def __init__(self, email: str):
        self.email = email
    def initials(self)->str:
        result = ''
        for word in self.email[:self.email.find('@')].split('.'):
            result = result + word[0]
        return result 

t = tttt('jasper.steenhuis@dinges.com')
print (t.initials)
