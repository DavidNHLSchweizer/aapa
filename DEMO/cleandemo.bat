@echo off
cd c:\repos\aapa\DEMO
del /s *.pdf >cleandemo.out 2>NUL
del  .\FORMS\*.docx >>cleandemo.out 2>NUL
del  .\MAIL\*.docx >>cleandemo.out 2>NUL
del  .\MAIL\*.htm >>cleandemo.out 2>NUL
"C:\Program Files\7-Zip\7z.exe" x DEMO.ZIP -y >>cleandemo.out 