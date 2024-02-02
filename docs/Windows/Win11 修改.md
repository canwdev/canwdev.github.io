## 删除 Win11 小组件

参考 [不喜欢Windows 11的小组件功能？直接命令行彻底删除 - 蓝点网 (landiannews.com)](https://www.landiannews.com/archives/95616.html)

1.  打开管理员模式的命令提示符，然后执行下面的命令
2.  `winget uninstall MicrosoftWindows.Client.WebExperience_cw5n1h2txyewy`
3.  该操作可能需要联网，如果报错那就再执行一次
4. 或可以直接使用 Dism++ 删除 Appx 包

## Edge配置

推荐使用 [Edge 配置百科](https://www.52pojie.cn/thread-1762445-1-1.html)

要启用地址栏搜索建议，启用这两项：

- 启用搜索建议
- 允许来自本地提供商的建议

## 恢复旧版资源管理器 Ribbon UI

https://www.elevenforum.com/t/restore-classic-file-explorer-with-ribbon-in-windows-11.620/

保存为 `Restore_classic_File_Explorer_with_ribbon_for_current_user.reg`，仅适用于 23H2 以上系统，运行后注销或重启资源管理器
```reg
Windows Registry Editor Version 5.00

; Created by: Shawn Brink
; Cretead on: January 11, 2024
; Tutorial: https://www.elevenforum.com/t/restore-classic-file-explorer-with-ribbon-in-windows-11.620/

[HKEY_CURRENT_USER\Software\Classes\CLSID\{2aa9162e-c906-4dd9-ad0b-3d24a8eef5a0}]
@="CLSID_ItemsViewAdapter"

[HKEY_CURRENT_USER\Software\Classes\CLSID\{2aa9162e-c906-4dd9-ad0b-3d24a8eef5a0}\InProcServer32]
@="C:\\Windows\\System32\\Windows.UI.FileExplorer.dll_"
"ThreadingModel"="Apartment"

[HKEY_CURRENT_USER\Software\Classes\CLSID\{6480100b-5a83-4d1e-9f69-8ae5a88e9a33}]
@="File Explorer Xaml Island View Adapter"

[HKEY_CURRENT_USER\Software\Classes\CLSID\{6480100b-5a83-4d1e-9f69-8ae5a88e9a33}\InProcServer32]
@="C:\\Windows\\System32\\Windows.UI.FileExplorer.dll_"
"ThreadingModel"="Apartment"
```

还原Win11资源管理器 `Default_modern_File_Explorer_with_command_bar_for_current_user.reg`
```reg
Windows Registry Editor Version 5.00

; Created by: Shawn Brink
; Cretead on: January 11, 2024
; Tutorial: https://www.elevenforum.com/t/restore-classic-file-explorer-with-ribbon-in-windows-11.620/

[-HKEY_CURRENT_USER\Software\Classes\CLSID\{2aa9162e-c906-4dd9-ad0b-3d24a8eef5a0}]

[-HKEY_CURRENT_USER\Software\Classes\CLSID\{6480100b-5a83-4d1e-9f69-8ae5a88e9a33}]
```