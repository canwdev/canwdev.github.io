WSL 2 在关闭终端后会自动休眠退出，无法直接常驻后台，这会影响后台服务与 Docker 的持续运行。因此，需要将其配置为开机自启并保持后台常驻。

以管理员身份运行：

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -NoProfile -Command `"wsl --distribution Debian`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME" -Delay (New-TimeSpan -Seconds 3)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "WSL Auto Start Debian" -Action $action -Trigger $trigger -Principal $principal -Description "Keep WSL Debian running"

# 验证
Get-ScheduledTask -TaskName "WSL Auto Start Debian"

# 手动触发测试
Start-ScheduledTask -TaskName "WSL Auto Start Debian"

# 打开计划任务程序验证
taskschd.msc

# 检查 WSL 状态
wsl --list --verbose
```

这个计划任务会创建一个隐形的 PowerShell 进程，内部运行 `wsl --distribution Debian`。只要该进程不退出，WSL 就不会自动停止。
