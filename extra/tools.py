from pathlib import Path
import re

def get_json_filename(module_file: str)->str:
    MnnnPATTERN = r"^m\d\d\d_(?P<module>.*)" 
    base = Path(module_file).stem
    if match := re.match(MnnnPATTERN, base, re.IGNORECASE):
        base = match.group('module')
    return f'{base}.json'

if __name__ == "__main__":       
    print(get_json_filename(f'extra\\strong'))
    print(get_json_filename(f'extra\\m25_strong'))
    print(get_json_filename(f'extra\\m252_strong'))