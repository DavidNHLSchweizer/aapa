from hashlib import file_digest 

def hash_file_digest(filename)->str:
    with open(filename, "rb") as file:
        return file_digest(file, 'sha3_256').hexdigest()
    
