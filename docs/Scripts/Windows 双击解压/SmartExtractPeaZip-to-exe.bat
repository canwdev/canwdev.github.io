@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build\bat2exe.ps1" ^
  -bat "%~dp0SmartExtractPeaZip.bat" ^
  -icon "C:\Program Files\PeaZip\peazip.exe" ^
  -out "%~dp0SmartExtractPeaZip.exe"

exit /b %ERRORLEVEL%
