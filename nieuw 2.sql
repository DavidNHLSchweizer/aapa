select SD.id,SD.directory,MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,F.filetype,F.mijlpaal_type
from STUDENT_DIRECTORY as SD 
inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.id=SDD.stud_dir_id 
inner join MIJLPAAL_DIRECTORY as MD on MD.id=SDD.mp_dir_id
inner join MIJLPAAL_DIRECTORY_FILES as MDF on MD.ID=MDF.mp_dir_id
inner join FILES as F on F.ID=MDF.file_id