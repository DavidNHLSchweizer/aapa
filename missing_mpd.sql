select S.id as stud_id,full_name,SD.id as SD_id,SD.directory as stud_dir,MPD.id as mp_id,MPD.mijlpaal_type,MPD.directory as "mp_directory",MPD.datum 
from studenten as S
inner join STUDENT_DIRECTORIES as SD on SD.stud_id = S.ID
inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.ID = SDD.stud_dir_id
inner join MIJLPAAL_DIRECTORIES as MPD on MPD.id = SDD.mp_dir_id
where mijlpaal_type = 1 and stud_dir <> mp_directory
