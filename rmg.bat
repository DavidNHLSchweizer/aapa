@echo off
call m125 %1 %2 %3
set basedir="D:\onedrive\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw\aapa"
copy /y %basedir%\aapa.db 
copy /y %basedir%\aapa.db testing123.db

