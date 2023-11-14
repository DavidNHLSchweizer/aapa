@echo off
set db0=aapa.db
set db1=testing123.db
set v0=1.18
set v1=1.19
copy /y %db0% %db1%
python aapa_migrate.py %db1% %v0% %v1%

