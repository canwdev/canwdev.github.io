@echo off
set "ZIP_PATH=C:\Program Files\7-Zip\7zg.exe"

:loop
if "%~1"=="" goto end
start "" "%ZIP_PATH%" x "%~1" -o"%~dp1"
shift
goto loop

:end
exit
