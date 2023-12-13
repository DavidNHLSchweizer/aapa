from database.dbConst import EMPTY_ID

class AAPAclass:
    def __init__(self, id=EMPTY_ID):
        self.id = id
    def relevant_attributes(self)->set[str]:
        #override in subclass if not all attributes are relevant, in particular for database equality
        return {attr for attr in dir(self) if attr[0] != '_'}
