def sop(n: int, singular: str, plural: str)->str:
    if n is None:
        return singular
    else:
        return singular if n==1 else plural
    