def sop(n: int, singular: str, plural: str, include_value = True)->str:
    if n is None:
        sop_str = singular
    else:
        sop_str = singular if n==1 else plural
    return f'{n} {sop_str}' if include_value else sop_str

    