@echo off
set basedir="D:\onedrive0\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw\aapa"
set db0=%basedir%\aapa_122.db
set db1=%basedir%\aapa.db
set v0=1.22
set v1=1.23

set phase1=%1
set phase2=%2
if "%2"=="" set phase2=%phase1%
set msg=Phases %phase1% to %phase2%
if "%1"=="" (
   set phase1=0
   set phase2=42
   set msg=All phases
)
@echo AAPA MIGRATION SCRIPT %v0% to %v1%. %msg%

goto :phase%phase1%

:phase0
set phase=0
call :migrate %phase%
call :msgnext
call :extra set_sdir_status
call :extra mp_dir_datum
if "%phase2%" LSS "1" goto :phase42

:phase1
set phase=1
call :migrate %phase%
call :msgnext
call :extra adapt_mp_dirs
if "%phase2%" LSS "2" goto :phase42

:phase2
set phase=2
call :migrate %phase%
call :msgnext
call :extra create_verslagen
if "%phase2%" LSS "3" goto :phase42

:phase3
set phase=3
call :migrate %phase%
call :msgnext
call :extra correct_stud_dirs
if "%phase2%" LSS "4" goto :phase42

:phase4
set phase=4
call :migrate %phase%
goto :phase42

:extra 
python run_extra.py m123_%~1 --onedrive=d:\onedrive0 --migrate=d:\aapa\migrate\m123
exit /b

:reset
copy /y %db0% %db1% >NUL
exit /b

:migrate
echo ---------------------------
echo --- MIGRATION PHASE %~1 ---
echo ---------------------------
call :reset
python aapa_migrate.py %db1% %v0% %v1% --phase=%~1
exit /b

:msgnext
set /a next=phase+1
echo ---------------------------------------------
echo --- preparing JSON files for phase %next% ---
echo ---------------------------------------------
exit /b

:phase42
set phase1=
set phase2=
