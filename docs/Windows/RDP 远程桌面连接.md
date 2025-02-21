
- [[RDP 在远程桌面连接服务中使用自定义证书加密]]

## 修改默认 RDP 端口号

来源：[tiny10 和 tiny11 23H2 的 Windows DD 镜像 | 秋水逸冰](https://teddysun.com/709.html)

将以下内容保存为 3389.bat
```bat
@echo off
>NUL 2>&1 REG.exe query "HKU\S-1-5-19" || (
    ECHO SET UAC = CreateObject^("Shell.Application"^) > "%TEMP%\Getadmin.vbs"
    ECHO UAC.ShellExecute "%~f0", "%1", "", "runas", 1 >> "%TEMP%\Getadmin.vbs"
    "%TEMP%\Getadmin.vbs"
    DEL /f /q "%TEMP%\Getadmin.vbs" 2>NUL
    Exit /b
)
color f0
echo Modify the remote desktop port and automatically add firewall rules
echo %date% %time%
set /p Port=Please enter a number (1024 - 65535):
if "%Port%"=="" goto end
goto edit
:edit
Reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\Wds\rdpwd\Tds\tcp" /v "PortNumber" /t REG_DWORD /d "%Port%" /f > nul
Reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v "PortNumber" /t REG_DWORD /d "%Port%" /f > nul
Reg add "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules" /v "{338933891-3389-3389-3389-338933893389}" /t REG_SZ /d "v2.29|Action=Allow|Active=TRUE|Dir=In|Protocol=6|LPort=%Port%|Name=Remote Desktop(TCP-In)|" /f > nul
Reg add "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules" /v "{338933892-3389-3389-3389-338933893389}" /t REG_SZ /d "v2.29|Action=Allow|Active=TRUE|Dir=In|Protocol=17|LPort=%Port%|Name=Remote Desktop(UDP-In)|" /f > nul
echo Success
echo Now new RDP port is: %Port%
echo Please restart computer
pause
exit
:end
echo Error. Please enter a correct number
pause
```

## RDP 使用空密码登录

在RDP主机上设置：

1. 按下“Win+R”打开“运行”输入 gpedit.msc
2. 点击“计算机配置”，“Windows设置”—>“安全设置”—>“本地策略”
	- 也可以在开始菜单 -> 管理工具 -> 本地安全策略
3. 点击右侧的“安全选项”
4. 双击“账户：使用空密码的本地账户只允许进行控制台登陆”
	- 英文版为：Account: Limit local account use of blank passwords to console login only
5. 选择“已禁用”点击“确定”即可
6. 参考： https://www.jb51.net/os/win10/746086.html

## RDP 究极优化技巧

- [Pushing Remote FX to its limits. : r/sysadmin](https://www.reddit.com/r/sysadmin/comments/fv7d12/pushing_remote_fx_to_its_limits/)
- [RDP 有什么究极优化技巧吗？ - V2EX](https://www.v2ex.com/t/987529)

TurboRemoteFXHost.reg
```reg
Windows Registry Editor Version 5.00

;Sets 60 FPS limit on RDP.
;Source: https://support.microsoft.com/en-us/help/2885213/frame-rate-is-limited-to-30-fps-in-windows-8-and-windows-server-2012-r

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations]

"DWMFRAMEINTERVAL"=dword:0000000f

;Increase Windows Responsivness
;Source:https://www.reddit.com/r/killerinstinct/comments/4fcdhy/an_excellent_guide_to_optimizing_your_windows_10/

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile]

"SystemResponsiveness"=dword:00000000

;Sets the flow control for Display vs Channel Bandwidth (aka RemoteFX devices, including controllers.)

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\TermDD]

"FlowControlDisable"=dword:00000001

"FlowControlDisplayBandwidth"=dword:0000010

"FlowControlChannelBandwidth"=dword:0000090

"FlowControlChargePostCompression"=dword:00000000

;Removes the artificial latency delay for RDP.

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp]

"InteractiveDelay"=dword:00000000

;Disables Windows Network Throtelling.

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters]

"DisableBandwidthThrottling"=dword:00000001

;Enables large MTU packets.

"DisableLargeMtu"=dword:00000000

;Disables the WDDM Drivers and goes back to legacy XDDM drivers. (better for performance on Nvidia cards, you might want to change this setting for AMD cards.)

[HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services]

"fEnableWddmDriver"=dword:00000000
```
## RDP 配置文件

- - 完整的配置可以参考 [Supported RDP properties | Microsoft Learn](https://learn.microsoft.com/en-us/azure/virtual-desktop/rdp-properties)
- [[Hyper-V 其他#使用 [RemoteApp](https //github.com/kimmknight/remoteapptool) 连接 Windows 虚拟机]]