@echo off
title WebDAV Server

set USER=admin
set PASS=yourpassword
set ADDR=0.0.0.0:8088

echo ========================================
echo   WebDAV Server Started
echo   Share: %cd%
echo   URL: http://%COMPUTERNAME%:%ADDR%
echo   User: %USER%
echo   Pass: %PASS%
echo ========================================
echo.
echo   Press Ctrl+C to stop server
echo ========================================
echo.

rclone serve webdav "%cd%" ^
    --addr %ADDR% ^
    --user %USER% ^
    --pass %PASS% ^
    --vfs-cache-mode off ^
    --dir-cache-time 1s ^
    --poll-interval 1s

if errorlevel 1 (
    echo.
    echo [ERROR] rclone command failed.
    echo Please check if rclone.exe is in PATH.
    echo.
    pause
)