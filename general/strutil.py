def replace_all(s: str, replace_chars: str, replace_with: str)->str:
    result = s
    for c in replace_chars:
        result = result.replace(c, replace_with)
    return result
