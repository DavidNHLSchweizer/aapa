@echo off
set db0=aapa.db
set db1=testing123.db
set v0=1.18
set v1=1.19
set v2=1.20
set v3=1.21
copy /y %db0% %db1%
python aapa_migrate.py %db1% %v0% %v1% 
python aapa_migrate.py %db1% %v1% %v2% -debug %1 %2 %3
python aapa_migrate.py %db1% %v2% %v3% -debug %1 %2 %3


