CREATE VIEW STUDENT_VERSLAGEN_OVERZICHT AS select (select full_name from STUDENTEN as S where S.id=V.stud_id) as student, V.datum, 
(case V.verslag_type when 0 then "" when 1 then "aanvraag" when 2 then "plan van aanpak" when 3 then "onderzoeksverslag" when 4 then "technisch verslag" when 5 then "eindverslag" when 6 then "productbeoordeling" when 7 then "presentatie" when 8 then "eindbeoordeling" when 9 then "afstudeerzitting" else "?" end ) 
as verslag_type, 
(select name from BEDRIJVEN as B where B.id=V.bedrijf_id) as bedrijf, V.titel,V.kans, 
(case V.status when -2 then "erfenis" when -1 then "ongeldig" when 0 then "nieuw" when 1 then "te beoordelen" when 2 then "bijlage" when 3 then "beoordeeld" when 4 then "geheel verwerkt" else "?" end ) 
as status,
(case V.beoordeling when 0 then "" when 1 then "onvoldoende" when 2 then "voldoende" else "?" end ) 
as beoordeling 
from VERSLAGEN as V order by 1,2