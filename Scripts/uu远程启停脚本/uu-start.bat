@echo off
title Start GameViewer Service and Application

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
:: Start Actions
:: ==========================================
echo ==================================================
echo   Starting GameViewer services and applications...
echo ==================================================
echo.

:: 1. Set service to Manual and Start it
echo [1/2] Configuring and starting GameViewerService...
sc config "GameViewerService" start= demand >nul 2>&1
net start "GameViewerService" >nul 2>&1
echo Status: Service set to Manual and started.

echo.

:: 2. Start the main application
echo [2/2] Launching GameViewer application...
start "" "C:\Program Files\Netease\GameViewer\GameViewer.exe"
echo Status: Application launched.

echo.
echo ==================================================
echo Task Completed Successfully!
echo ==================================================
echo.
timeout /t 3