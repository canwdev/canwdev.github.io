@echo off
netsh int ip set address name="WLAN" static 172.20.10.2 255.255.255.0 172.20.10.1
pause