def sop(n9: int, singular: str, plural: str)->str:
    if n9 is None:
        return singular
    else:
        return singular if n9==1 else plural
    