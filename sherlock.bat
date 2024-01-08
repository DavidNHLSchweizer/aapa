@rem set preview=-preview
@set preview=
@rem niet op preview zetten, de stud_dir ids moeten worden gegenereerd via de database!
@rem daarna wel weer opnieuw migreren
@set start=%1
@set finish=%2
@echo Starting SHERLOCK...>sherlock.log
@DATE/T>>sherlock.log
@TIME/T>>sherlock.log
@if "%start%" NEQ "" echo start %start% >>sherlock.log
@@if "%finish%" NEQ "" echo finish %finish% >>sherlock.log

@if "%start%" NEQ "" GOTO %start%
@rem error handling too complicated, just type in the right label pls

@:1
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1" --migrate="data\migrate\m119" > detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "1" GOTO :eof
@:2
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "2" GOTO :eof
@:3
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "3" GOTO :eof
@:4
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "4" GOTO :eof
@:5
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "5" GOTO :eof
@:6
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "6" GOTO :eof
@:7
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "7" GOTO :eof
@:8
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "8" GOTO :eof
@:9
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "9" GOTO :eof
@:10
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "10" GOTO :eof
@:11
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "11" GOTO :eof
@:12
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Oud" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@if "%finish%" EQU "12" GOTO :eof
@:13
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
