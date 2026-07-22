@echo off
set "PEAZIP_PATH=C:\Program Files\PeaZip\peazip.exe"

:loop
if "%~1"=="" goto end
start "" "%PEAZIP_PATH%" -ext2smart "%~1"
shift
goto loop

:end
exit