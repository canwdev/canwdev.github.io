@echo off
netsh int ip set address name="WLAN" static 192.168.0.100 255.255.255.0 192.168.0.1
pause