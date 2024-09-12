
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