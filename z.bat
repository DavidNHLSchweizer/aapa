call :test 3 6 5
call :test 426 5
call :test 42
goto :eof

:test
@set naaigaren=param1%~1
@echo test!
@echo %naaigaren%
@echo param12=%~2
@echo param3=%~3
exit /b
