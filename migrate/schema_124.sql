AAPA Database schema versie 1.24
20-02-2024 16:58:49

table VERSIE:
  CREATE TABLE IF NOT EXISTS VERSIE (ID INTEGER PRIMARY KEY,db_versie TEXT,versie TEXT,datum TEXT);
table FILEROOT:
  CREATE TABLE IF NOT EXISTS FILEROOT (ID INTEGER PRIMARY KEY,code TEXT UNIQUE,root TEXT);
table STUDENTEN:
  CREATE TABLE IF NOT EXISTS STUDENTEN (id INTEGER PRIMARY KEY,stud_nr TEXT,full_name TEXT,first_name TEXT,email TEXT
  NOT NULL,status INTEGER);
table BEDRIJVEN:
  CREATE TABLE IF NOT EXISTS BEDRIJVEN (id INTEGER PRIMARY KEY,name TEXT);
table AANVRAGEN:
  CREATE TABLE IF NOT EXISTS AANVRAGEN (id INTEGER PRIMARY KEY,datum TEXT,stud_id INTEGER,bedrijf_id INTEGER,titel
  TEXT,kans INTEGER,status INTEGER,beoordeling INTEGER,datum_str TEXT,versie INTEGER,FOREIGN KEY(stud_id) REFERENCES
  STUDENTEN(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN KEY(bedrijf_id) REFERENCES BEDRIJVEN(id) ON UPDATE CASCADE
  ON DELETE CASCADE);
table AANVRAGEN_FILES:
  CREATE TABLE IF NOT EXISTS AANVRAGEN_FILES (aanvraag_id INTEGER,file_id INTEGER,PRIMARY
  KEY(aanvraag_id,file_id),FOREIGN KEY(aanvraag_id) REFERENCES AANVRAGEN(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN
  KEY(file_id) REFERENCES FILES(id) ON UPDATE CASCADE ON DELETE CASCADE);
table FILES:
  CREATE TABLE IF NOT EXISTS FILES (id INTEGER PRIMARY KEY,filename TEXT,timestamp TEXT,digest TEXT,filetype
  INTEGER,mijlpaal_type INTEGER); CREATE INDEX IF NOT EXISTS name_index ON FILES(filename);
table UNDOLOGS:
  CREATE TABLE IF NOT EXISTS UNDOLOGS (id INTEGER PRIMARY KEY,description TEXT,action INTEGER,processing_mode
  INTEGER,user TEXT,date TEXT,can_undo INTEGER);
table UNDOLOGS_AANVRAGEN:
  CREATE TABLE IF NOT EXISTS UNDOLOGS_AANVRAGEN (log_id INTEGER,aanvraag_id INTEGER,PRIMARY
  KEY(log_id,aanvraag_id),FOREIGN KEY(log_id) REFERENCES UNDOLOGS(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN
  KEY(aanvraag_id) REFERENCES AANVRAGEN(id) ON UPDATE CASCADE ON DELETE CASCADE);
table UNDOLOGS_VERSLAGEN:
  CREATE TABLE IF NOT EXISTS UNDOLOGS_VERSLAGEN (log_id INTEGER,verslag_id INTEGER,PRIMARY
  KEY(log_id,verslag_id),FOREIGN KEY(log_id) REFERENCES UNDOLOGS(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN
  KEY(verslag_id) REFERENCES VERSLAGEN(id) ON UPDATE CASCADE ON DELETE CASCADE);
table UNDOLOGS_FILES:
  CREATE TABLE IF NOT EXISTS UNDOLOGS_FILES (log_id INTEGER,file_id INTEGER,PRIMARY KEY(log_id,file_id),FOREIGN
  KEY(log_id) REFERENCES UNDOLOGS(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN KEY(file_id) REFERENCES FILES(id) ON
  UPDATE CASCADE ON DELETE CASCADE);
table VERSLAGEN:
  CREATE TABLE IF NOT EXISTS VERSLAGEN (id INTEGER PRIMARY KEY,datum TEXT,stud_id INTEGER,bedrijf_id INTEGER,titel
  TEXT,kans INTEGER,status INTEGER,beoordeling INTEGER,verslag_type INTEGER,cijfer TEXT,FOREIGN KEY(stud_id) REFERENCES
  STUDENTEN(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN KEY(bedrijf_id) REFERENCES BEDRIJVEN(id) ON UPDATE CASCADE
  ON DELETE CASCADE);
table VERSLAGEN_FILES:
  CREATE TABLE IF NOT EXISTS VERSLAGEN_FILES (verslag_id INTEGER,file_id INTEGER,PRIMARY KEY(verslag_id,file_id),FOREIGN
  KEY(verslag_id) REFERENCES VERSLAGEN(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN KEY(file_id) REFERENCES FILES(id)
  ON UPDATE CASCADE ON DELETE CASCADE);
table BASEDIRS:
  CREATE TABLE IF NOT EXISTS BASEDIRS (id INTEGER PRIMARY KEY,year INTEGER,period TEXT,forms_version TEXT,directory
  TEXT);
table STUDENT_DIRECTORIES:
  CREATE TABLE IF NOT EXISTS STUDENT_DIRECTORIES (id INTEGER PRIMARY KEY,stud_id INTEGER,directory TEXT,basedir_id
  INTEGER,status INTEGER,FOREIGN KEY(stud_id) REFERENCES STUDENTEN(id) ON UPDATE CASCADE ON DELETE CASCADE,FOREIGN
  KEY(basedir_id) REFERENCES BASEDIRS(id) ON UPDATE CASCADE ON DELETE CASCADE);
table STUDENT_DIRECTORY_DIRECTORIES:
  CREATE TABLE IF NOT EXISTS STUDENT_DIRECTORY_DIRECTORIES (stud_dir_id INTEGER,mp_dir_id INTEGER,PRIMARY
  KEY(stud_dir_id,mp_dir_id),FOREIGN KEY(stud_dir_id) REFERENCES STUDENT_DIRECTORIES(id) ON UPDATE CASCADE ON DELETE
  CASCADE,FOREIGN KEY(mp_dir_id) REFERENCES MIJLPAAL_DIRECTORY(id) ON UPDATE CASCADE ON DELETE CASCADE);
table MIJLPAAL_DIRECTORIES:
  CREATE TABLE IF NOT EXISTS MIJLPAAL_DIRECTORIES (id INTEGER PRIMARY KEY,mijlpaal_type INTEGER,kans INTEGER,directory
  TEXT,datum TEXT);
table MIJLPAAL_DIRECTORY_FILES:
  CREATE TABLE IF NOT EXISTS MIJLPAAL_DIRECTORY_FILES (mp_dir_id INTEGER,file_id INTEGER,PRIMARY
  KEY(mp_dir_id,file_id),FOREIGN KEY(mp_dir_id) REFERENCES MIJLPAAL_DIRECTORIES(id) ON UPDATE CASCADE ON DELETE
  CASCADE,FOREIGN KEY(file_id) REFERENCES FILES(id) ON UPDATE CASCADE ON DELETE CASCADE);

view AANVRAGEN_OVERZICHT:
  CREATE VIEW IF NOT EXISTS AANVRAGEN_OVERZICHT AS select id,(select full_name from STUDENTEN as S where S.ID =
  A.stud_id) as student,datum,(select name from BEDRIJVEN as B where B.ID = A.bedrijf_id) as
  bedrijf,titel,versie,kans,(case beoordeling when 0 then "" when 1 then "onvoldoende" when 2 then "voldoende" else "?"
  end ) as beoordeling from AANVRAGEN as A order by 2,3;
view AANVRAGEN_FILE_OVERZICHT:
  CREATE VIEW IF NOT EXISTS AANVRAGEN_FILE_OVERZICHT AS select A.id as aanvraag_id,(select full_name from STUDENTEN as S
  where S.ID = A.stud_id) as student,titel, F.ID as file_id,F.filename as filename,(case F.filetype when -4 then
  "directory (geen verdere gegevens)" when -3 then "docx-bestand (geen verdere gegevens)" when -2 then "pdf-bestand
  (geen verdere gegevens)" when -1 then "!unknown" when 0 then "PDF-file (aanvraag)" when 1 then "Beoordelingsformulier"
  when 2 then "Kopie van PDF-file (aanvraag)" when 3 then "Verschilbestand met vorige versie aanvraag" when 5 then
  "Ingevuld beoordelingsformulier (PDF format)" when 6 then "Beoordelingsformulier (examinator 1)" when 7 then
  "Beoordelingsformulier (examinator 2)" when 8 then "Beoordelingsformulier (examinator 3 of hoger)" when 9 then "Plan
  van Aanpak" when 10 then "Onderzoeksverslag" when 11 then "Technisch verslag" when 12 then "Eindverslag" when 13 then
  "Aanvraag" when 20 then "PDF bestand" when 21 then "Microsoft Word bestand" else "?" end ) as filetype from AANVRAGEN
  as A inner join AANVRAGEN_FILES as AF on A.ID=AF.aanvraag_id inner join FILES as F on F.ID=AF.file_id order by 2;
view STUDENT_DIRECTORIES_FILE_OVERZICHT:
  CREATE VIEW IF NOT EXISTS STUDENT_DIRECTORIES_FILE_OVERZICHT AS select SD.id,SD.STUD_ID,SD.directory as
  student_directory,(case sd.status when 0 then "nog niet bekend" when 1 then "actief" when 42 then "gearchiveerd" else
  "?" end ) as dir_status,MD.id as mp_id,MD.directory as mp_dir,F.ID as file_id,F.filename,(case F.filetype when -4 then
  "directory (geen verdere gegevens)" when -3 then "docx-bestand (geen verdere gegevens)" when -2 then "pdf-bestand
  (geen verdere gegevens)" when -1 then "!unknown" when 0 then "PDF-file (aanvraag)" when 1 then "Beoordelingsformulier"
  when 2 then "Kopie van PDF-file (aanvraag)" when 3 then "Verschilbestand met vorige versie aanvraag" when 5 then
  "Ingevuld beoordelingsformulier (PDF format)" when 6 then "Beoordelingsformulier (examinator 1)" when 7 then
  "Beoordelingsformulier (examinator 2)" when 8 then "Beoordelingsformulier (examinator 3 of hoger)" when 9 then "Plan
  van Aanpak" when 10 then "Onderzoeksverslag" when 11 then "Technisch verslag" when 12 then "Eindverslag" when 13 then
  "Aanvraag" when 20 then "PDF bestand" when 21 then "Microsoft Word bestand" else "?" end ) as filetype,(case
  F.mijlpaal_type when 0 then "" when 1 then "aanvraag" when 2 then "plan van aanpak" when 3 then "onderzoeksverslag"
  when 4 then "technisch verslag" when 5 then "eindverslag" when 6 then "productbeoordeling" when 7 then "presentatie"
  when 8 then "eindbeoordeling" when 9 then "afstudeerzitting" else "?" end ) as mijlpaal from STUDENT_DIRECTORIES as SD
  inner join STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.id=SDD.stud_dir_id inner join MIJLPAAL_DIRECTORIES as MD on
  MD.id=SDD.mp_dir_id inner join MIJLPAAL_DIRECTORY_FILES as MDF on MD.ID=MDF.mp_dir_id inner join FILES as F on
  F.ID=MDF.file_id;
view STUDENT_DIRECTORIES_OVERZICHT:
  CREATE VIEW IF NOT EXISTS STUDENT_DIRECTORIES_OVERZICHT AS select s.id,full_name,stud_nr,(case s.status when 0 then
  "nog niet bekend" when 1 then "aanvraag gedaan" when 2 then "bezig met afstuderen" when 3 then "afgestudeerd" when 10
  then "gestopt" else "?" end ) as student_status,bd.year,bd.period,sdd.directory as "(laatste) directory" from
  studenten as s inner join student_directories as sdd on s.id = sdd.stud_id inner join basedirs as bd on sdd.basedir_id
  = bd.id group by sdd.stud_id having max(sdd.id) order by 5,6,2;
view STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT:
  CREATE VIEW IF NOT EXISTS STUDENT_MIJLPAAL_DIRECTORIES_OVERZICHT AS select (select full_name from studenten as S where
  S.id=SD.stud_id) as student, MPD.datum, (case MPD.mijlpaal_type when 0 then "" when 1 then "aanvraag" when 2 then
  "plan van aanpak" when 3 then "onderzoeksverslag" when 4 then "technisch verslag" when 5 then "eindverslag" when 6
  then "productbeoordeling" when 7 then "presentatie" when 8 then "eindbeoordeling" when 9 then "afstudeerzitting" else
  "?" end ) as mijlpaal_type, MPD.kans, MPD.directory from student_directories as SD inner join
  STUDENT_DIRECTORY_DIRECTORIES as SDD on SD.ID=SDD.stud_dir_id inner join MIJLPAAL_DIRECTORIES MPD on
  MPD.ID=SDD.mp_dir_id order by 1,3;