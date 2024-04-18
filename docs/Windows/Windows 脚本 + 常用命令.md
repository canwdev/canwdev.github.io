## Win+R 常用运行命令

- `control` 控制面板
- `regedit` 注册表编辑器
- `eventvwr` 事件查看器
- `mmc` Microsoft 管理控制台
- `gpedit.msc` 组策略
- `devmgmt.msc` 设备管理器
- `diskmgmt.msc` 磁盘管理
- `services.msc` 服务
- `certmgr.msc` 证书
- `taskschd.msc` 计划任务程序
- `wf.msc` 高级安全 Windows 防火墙
- `%windir%\explorer.exe shell:::{4234d49b-0245-4df3-b780-3893943456e1}` 打开 Applications 目录

## Windows 端口占用查询

1. 查看 1080 端口的占用情况：`netstat -aon|findstr "1080"`
2. 根据 PID 找到应用程序：`tasklist|findstr "9820"`

## 在 Powershell 安装 oh-my-posh
[[Powershell 如何安装 OnMyPosh]]

## 无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本
使用管理权限运行命令：
```sh
set-executionpolicy remotesigned
```


## Win10 删除壁纸历史记录

运行 regedit，定位到 `计算机\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers`，里面有类似 `BackgroundHistoryPath` 这样的条目，可以直接删除。

## 一条命令关闭 Windows 显示器

```powershell
PowerShell -windowstyle hidden -command "(Add-Type -MemberDefinition "\"[DllImport(\"\"user32.dll\"\")]`npublic static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);"\" -Name \"Win32SendMessage\" -Namespace Win32Functions -PassThru)::SendMessage(0xffff, 0x0112, 0xF170, 2)"
```

## Win10 离线安装 .NET Framework 3.5（需要系统光盘）

选择和当前系统版本相同的原版 iso 系统光盘，右键“装载”，会有一个DVD驱动器，记住盘符，比如 `L:`

以管理员权限运行 PowerShell，输入如下命令（请确保盘符正确）即可自动安装。

```sh
dism.exe /online /enable-feature /featurename:netfx3 /Source:L:\sources\sxs
```

```
PS C:\Windows\system32> dism.exe /online /enable-feature /featurename:netfx3 /Source:G:\sources\sxs

部署映像服务和管理工具
版本: 10.0.17763.1

映像版本: 10.0.17763.316

启用一个或多个功能
[==========================100.0%==========================]
操作成功完成。
```

## Windows 递归修改文件夹权限为 Everyone

```sh
icacls "D:\CodeArchive" /grant Everyone:M /t
```

## Win 10 1803及以后版本的蓝牙音量（绝对音量）问题

```
1、win+r，输入regedit，打开注册表
2、进入路径：计算机\HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Bluetooth\Audio\AVRCP\CT
3、找到DisableAbsoluteVolume值，修改为1，如果没有，右键新建DWORD32位，建立对应值。
4、重启。
```


## Win 11 启动 IE 浏览器

`IE.vbs`
```vbs
CreateObject("InternetExplorer.Application").Visible=true
```

## Win 10 以上系统启动传统个性化面板

个性化.bat
```bat
start shell:::{ED834ED6-4B5A-4BfE-8F11-A626DCB6A921}
```

## 使用 .vbs 脚本启动 exe 程序

支持传参，并且不弹出 cmd 窗口

```vbs
strCommand = "cmd /c .\totalcmd\TOTALCMD64.EXE"

For Each Arg In WScript.Arguments
    strCommand = strCommand & " """ & replace(Arg, """", """""""""") & """"
Next

CreateObject("Wscript.Shell").Run strCommand, 0, false
```

## 修改远程桌面端口号为非3389

保存以下脚本为bat格式，以管理员权限运行：

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