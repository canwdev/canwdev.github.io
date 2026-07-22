@echo off
title rclone WebDAV Server + Client

set WEBDAV_URL=http://127.0.0.1:8080
set USER=admin
set PASS=yourpassword
set DRIVE_LETTER=Z
set SHARE_DIR=%cd%

:: ============================================================
:: Part 1: Start WebDAV server in a new window
:: ============================================================
echo [1] Starting WebDAV server...
start "WebDAV Server" cmd /c rclone serve webdav "%SHARE_DIR%" ^
    --addr 0.0.0.0:8080 ^
    --user %USER% ^
    --pass %PASS% ^
    --vfs-cache-mode off ^
    --dir-cache-time 1s ^
    --poll-interval 1s

timeout /t 2 /nobreak >nul

:: ============================================================
:: Part 2: Create rclone remote
:: ============================================================
echo [2] Creating WebDAV remote...
rclone config create webdav-remote webdav url %WEBDAV_URL% vendor other user %USER% pass %PASS% 2>nul

:: ============================================================
:: Part 3: Mount as Z: drive
:: ============================================================
echo [3] Mounting as %DRIVE_LETTER%: drive...
echo.
echo IMPORTANT: Write to Z: drive, check the original folder
echo Press Ctrl+C to unmount all and exit
echo ============================================================
echo.

rclone mount webdav-remote: %DRIVE_LETTER%: ^
    --vfs-cache-mode off ^
    --dir-cache-time 1s ^
    --poll-interval 1s ^
    --buffer-size 0 ^
    --network-mode ^
    --attr-timeout 0

:: ============================================================
:: Cleanup: kill server process when mount exits
:: ============================================================
taskkill /fi "windowtitle eq WebDAV Server" /f >nul 2>nul