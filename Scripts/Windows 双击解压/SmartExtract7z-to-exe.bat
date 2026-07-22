@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build\bat2exe.ps1" ^
  -bat "%~dp0SmartExtract7z.bat" ^
  -icon "C:\Program Files\7-Zip\7zFM.exe" ^
  -out "%~dp0SmartExtract7z.exe"

exit /b %ERRORLEVEL%
