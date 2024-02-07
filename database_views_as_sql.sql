CREATE VIEW AANVRAGEN_FILE_OVERZICHT AS select A.id as aanvraag_id,(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student,
titel, F.ID as file_id,F.filename as filename,
(case F.filetype when -4 then "directory (geen verdere gegevens)" when -3 then "docx-bestand (geen verdere gegevens)" when -2 then "pdf-bestand (geen verdere gegevens)" when -1 then "!unknown" when 0 then "PDF-file (aanvraag)" when 1 then "Beoordelingsformulier" when 2 then "Kopie van PDF-file (aanvraag)" when 3 then "Verschilbestand met vorige versie aanvraag" when 5 then "Ingevuld beoordelingsformulier (PDF format)" when 6 then "Beoordelingsformulier (examinator 1)" when 7 then "Beoordelingsformulier (examinator 2)" when 8 then "Beoordelingsformulier (examinator 3 of hoger)" when 9 then "Plan van Aanpak" when 10 then "Onderzoeksverslag" when 11 then "Technisch verslag" when 12 then "Eindverslag" when 13 then "Aanvraag" else "?" end ) 
as filetype                                 
from AANVRAGEN as A  inner join AANVRAGEN_FILES as AF on A.ID=AF.aanvraag_id inner join FILES as F on F.ID=AF.file_id order by 2

CREATE VIEW AANVRAGEN_OVERZICHT AS select id,(select full_name from STUDENTEN as S where S.ID = A.stud_id) as student,
datum,(select name from BEDRIJVEN as B where B.ID = A.bedrijf_id) as bedrijf,titel,versie,kans,
(case beoordeling when 0 then "" when 1 then "onvoldoende" when 2 then "voldoende" else "?" end ) as beoordeling 
from AANVRAGEN as A order by 2,3

CREATE VIEW STUDENT_DIRECTORIES_FILE_OVERZICHT AS select SD.id,SD.STUD_ID, SD.directory,MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,
(case F.filetype when -4 then "directory (geen verdere gegevens)" when -3 then "docx-bestand (geen verdere gegevens)" when -2 then "pdf-bestand (geen verdere gegevens)" when -1 then "!unknown" when 0 then "PDF-file (aanvraag)" when 1 then "Beoordelingsformulier" when 2 then "Kopie van PDF-file (aanvraag)" when 3 then "Verschilbestand met vorige versie aanvraag" when 5 then "Ingevuld beoordelingsformulier (PDF format)" when 6 then "Beoordelingsformulier (examinator 1)" when 7 then "Beoordelingsformulier (examinator 2)" when 8 then "Beoordelingsformulier (examinator 3 of hoger)" when 9 then "Plan van Aanpak" when 10 then "Onderzoeksverslag" when 11 then "Technisch verslag" when 12 then "Eindverslag" when 13 then "Aanvraag" else "?" end ) 
as filetype,
(case F.mijlpaal_type when 0 then "" when 1 then "aanvraag" when 2 then "plan van aanpak" when 3 then "onderzoeksverslag" when 4 then "technisch verslag" when 5 then "eindverslag" when 6 then "productbeoordeling" when 7 then "presentatie" when 8 then "eindbeoordeling" when 9 then "afstudeerzitting" else "?" end ) 
as mijlpaal 
from "OLD_STUDENT_DIRECTORIES" as SD 
inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.id=SDD.stud_dir_id 
inner join MIJLPAAL_DIRECTORIES as MD on MD.id=SDD.mp_dir_id 
inner join MIJLPAAL_DIRECTORY_FILES as MDF on MD.ID=MDF.mp_dir_id 
inner join FILES as F on F.ID=MDF.file_id

CREATE VIEW STUDENT_DIRECTORIES_OVERZICHT AS select s.id,full_name,stud_nr,
(case s.status when 0 then "nog niet bekend" when 1 then "aanvraag gedaan" when 2 then "bezig met afstuderen" when 3 then "afgestudeerd" when 10 then "gestopt" else "?" end ) 
as status,
bd.year,bd.period,sdd.directory as "(laatste) directory" 
from studenten as s 
inner join "OLD_STUDENT_DIRECTORIES" as sdd on s.id = sdd.stud_id 
inner join basedirs as bd on sdd.basedir_id = bd.id 
group by sdd.stud_id 
having max(sdd.id) order by 5,6,2

CREATE VIEW STUDENT_VERSLAGEN_OVERZICHT AS select (select full_name from STUDENTEN as S where S.id=V.stud_id) as student, V.datum, 
(case V.verslag_type when 0 then "" when 1 then "aanvraag" when 2 then "plan van aanpak" when 3 then "onderzoeksverslag" when 4 then "technisch verslag" when 5 then "eindverslag" when 6 then "productbeoordeling" when 7 then "presentatie" when 8 then "eindbeoordeling" when 9 then "afstudeerzitting" else "?" end ) 
as verslag_type, 
(select name from BEDRIJVEN as B where B.id=V.bedrijf_id) as bedrijf, V.titel,V.kans, 
(case V.status when -2 then "erfenis" when -1 then "ongeldig" when 0 then "nieuw" when 1 then "te beoordelen" when 2 then "bijlage" when 3 then "beoordeeld" when 4 then "geheel verwerkt" else "?" end ) 
as status,
(case V.beoordeling when 0 then "" when 1 then "onvoldoende" when 2 then "voldoende" else "?" end ) 
as beoordeling 
from VERSLAGEN as V order by 1,2
