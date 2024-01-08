@set level=%1
@set finish=%2

@echo Starting SHERLOCK...>sherlock.dum
@DATE/T>>sherlock.dum
@TIME/T>>sherlock.dum
if "%level%" NEQ "" echo Level %level% >>sherlock.dum

@if "%level%" NEQ "" GOTO %level%
@:1
@echo Hallo 1
@if "%finish%" EQU "2" GOTO :eof
@:2
@echo Hallo 2
@if "%finish%" EQU "3" GOTO :eof
@:3
@echo Hallo 3

