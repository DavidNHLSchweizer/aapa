@echo off
del /s .\DEMO\*.pdf >cleandemo.out 2>NUL
del  DEMO\MAIL\*.pdf >>cleandemo.out 2>NUL
del  DEMO\MAIL\*.docx >>cleandemo.out 2>NUL
"C:\Program Files\7-Zip\7z.exe" x DEMO.ZIP >>cleandemo.out 