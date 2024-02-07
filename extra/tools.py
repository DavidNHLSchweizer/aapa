from pathlib import Path

def get_json_filename(module_file: str)->str:
    return f'{Path(module_file).stem}.json'