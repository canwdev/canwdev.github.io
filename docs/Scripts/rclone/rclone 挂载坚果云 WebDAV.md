```bat
@echo off
# CMD编码格式为UTF-8
chcp 65001
rem path=%~dp0
path=C:\Windows
@echo on
%path%\rclone config
pause
```

```bat
@echo off
# CMD编码格式为UTF-8
chcp 65001
rem path=%~dp0
path=C:\Windows
@echo on
%path%\rclone mount webdav_jmgo:/我的坚果云 J: --cache-dir D:\rclone_cache --vfs-cache-mode writes
pause
```