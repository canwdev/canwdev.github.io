- Win11 精简脚本：[Win-Debloat-Tools](https://github.com/LeDragoX/Win-Debloat-Tools)
- [Mindows一键激活.bat](https://syxz.lanzoub.com/iQ38c0nqmmva)

## Win11 开启平板模式任务栏

运行 regedit，定位到：
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\PriorityControl
```
里面有一个**ConvertibleSlateMode**，打开它，把里面的数值改为**1**，保存，再次打开并改为**0**。[参考](https://www.bilibili.com/opus/794446461839343651)
## 删除 Win11 小组件

参考 [不喜欢Windows 11的小组件功能？直接命令行彻底删除 - 蓝点网 (landiannews.com)](https://www.landiannews.com/archives/95616.html)

1.  打开管理员模式的命令提示符，然后执行下面的命令
2.  `winget uninstall MicrosoftWindows.Client.WebExperience_cw5n1h2txyewy`
3.  该操作可能需要联网，如果报错那就再执行一次
4. 或可以直接使用 Dism++ 删除 Appx 包

## Win11 OOBE 跳过联网

多种方法：
1. 在 oobe 界面按 shift+f10，弹出cmd，输入 `oobe\BypassNRO.cmd` 系统重启后就不用联网了。
2. 输入邮箱 `no@thankyou.com`
3. cmd 输入命令 `start ms-cxh:localonly`

BypassNRO.cmd 的有效代码如下：
```
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\OOBE /v BypassNRO /t REG_DWORD /d 1 /f
shutdown /r /t 0
```

## Win11 应用商店
[kinkim/InstallMicrosoftStoreOnLTSC: InstallMicrosoftStoreOnLTSC2019 (github.com)](https://github.com/kinkim/InstallMicrosoftStoreOnLTSC)

## 还原 Win11 新建文本菜单
```shell
reg.exe add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
```
## 恢复旧版资源管理器 Ribbon UI

- [参考](https://www.elevenforum.com/t/restore-classic-file-explorer-with-ribbon-in-windows-11.620/)
- 实际使用体验一般，建议使用 [StartAllBack](https://www.123pan.com/s/HQeA-xn1Sh)

保存为 `Restore_classic_File_Explorer_with_ribbon_for_current_user.reg`，仅适用于 23H2 以上系统，运行后注销或重启资源管理器
```reg
Windows Registry Editor Version 5.00

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

[HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\Toolbar\ShellBrowser]
"ITBar7Layout"=hex:13,00,00,00,00,00,00,00,00,00,00,00,20,00,00,00,10,00,01,00,\
  00,00,00,00,01,00,00,00,01,07,00,00,5e,01,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
  00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00
```

还原Win11资源管理器 `Default_modern_File_Explorer_with_command_bar_for_current_user.reg`
```reg
Windows Registry Editor Version 5.00

[-HKEY_CURRENT_USER\Software\Classes\CLSID\{2aa9162e-c906-4dd9-ad0b-3d24a8eef5a0}]

[-HKEY_CURRENT_USER\Software\Classes\CLSID\{6480100b-5a83-4d1e-9f69-8ae5a88e9a33}]
```

## Edge配置

推荐使用 [Edge 配置百科](https://www.52pojie.cn/thread-1762445-1-1.html)

要启用地址栏搜索建议，启用这两项：

- 启用搜索建议
- 允许来自本地提供商的建议
