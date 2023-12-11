def sop(n: int, singular: str, plural: str, include_value = True, prefix='')->str:
    if n is None:
        sop_str = singular
    else:
        sop_str = singular if n==1 else plural
    prefix_str = prefix if prefix else ""
    return f'{n} {prefix_str}{sop_str}' if include_value else f'{prefix_str}{sop_str}'

    