@echo off
title Stop and Disable GameViewer Service

:: ==========================================
:: Automatically Request Administrator Rights
:: ==========================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%cd%"
    CD /D "%~dp0"

:: ==========================================
:: Stop and Disable Actions
:: ==========================================
echo ==================================================
echo   Processing GameViewer services and processes...
echo ==================================================
echo.

:: 1. Disable and Stop the service
echo [1/3] Disabling and stopping GameViewerService...
sc config "GameViewerService" start= disabled >nul 2>&1
net stop "GameViewerService" >nul 2>&1
taskkill /f /im GameViewerService.exe >nul 2>&1
echo Status: Service has been disabled and stopped.

echo.

:: 2. Kill the main application process
echo [2/3] Terminating GameViewer.exe...
taskkill /f /im GameViewer.exe >nul 2>&1
echo Status: Main process terminated.

echo.

:: 3. Double check for remaining processes
echo [3/3] Checking for any remaining processes...
tasklist | findstr /i "GameViewer" >nul
if %errorlevel% equ 0 (
    echo Status: Found remaining processes, performing deep clean...
    wmic process where "name like 'GameViewer%%'" call terminate >nul 2>&1
) else (
    echo Status: All clean. No running processes found.
)

echo.
echo ==================================================
echo Task Completed Successfully!
echo ==================================================
echo.
pause