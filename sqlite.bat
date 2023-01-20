@echo off
set database=%1
if "%database%" =="" set database=aapa.db
c:\tools\sqlite\sqlite3.exe %database%