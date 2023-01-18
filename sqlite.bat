@echo off
set "curdir=%cd%"
cd c:\repos\aapa
echo "%cd%%1"
set database="%cd%%1"
if "%database%" =="" set database=aapa.db
c:\tools\sqlite\sqlite3.exe %database%
cd %curdir%