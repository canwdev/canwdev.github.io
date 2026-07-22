@echo off
title WebDAV Mount

:: ============================================================
:: EDIT THESE VALUES BEFORE RUNNING
:: ============================================================
set WEBDAV_URL=http://127.0.0.1:8088
set USER=admin
set PASS=yourpassword
set DRIVE_LETTER=Z
:: ============================================================

:: Check if rclone exists
where rclone >nul 2>nul
if errorlevel 1 (
    echo [ERROR] rclone not found in PATH.
    echo Please add rclone to PATH or use full path.
    pause
    exit /b 1
)

:: Create or update WebDAV remote
echo [INFO] Configuring WebDAV remote...
rclone listremotes 2>nul | findstr /i "webdav-remote" >nul
if errorlevel 1 (
    rclone config create webdav-remote webdav url %WEBDAV_URL% vendor other user %USER% pass %PASS%
) else (
    rclone config update webdav-remote url %WEBDAV_URL% vendor other user %USER% pass %PASS%
)

echo ========================================
echo   Mounting WebDAV as Drive %DRIVE_LETTER%:
echo   URL: %WEBDAV_URL%
echo   User: %USER%
echo ========================================
echo.
echo   Mount point: %DRIVE_LETTER%:\
echo   Write files here, check server folder
echo   Press Ctrl+C to unmount and exit
echo ========================================
echo.

rclone mount webdav-remote: %DRIVE_LETTER%: ^
    --vfs-cache-mode off ^
    --dir-cache-time 1s ^
    --poll-interval 1s ^
    --buffer-size 0 ^
    --network-mode ^
    --attr-timeout 0

if errorlevel 1 (
    echo.
    echo [ERROR] Mount failed.
    echo Please check if WinFsp is installed.
    echo Download: https://winfsp.dev/
    echo.
    pause
)