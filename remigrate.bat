@echo off
set basedir="D:\onedrive0\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw\aapa"
set db0=%basedir%\aapa_122.db
set db1=%basedir%\aapa.db
set v0=1.22
set v1=1.23
copy /y %db0% %db1%
python aapa_migrate.py %db1% %v0% %v1% 

