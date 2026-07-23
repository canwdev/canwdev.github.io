> Win 11 系统 bug 导致文件夹右键不显示「Open with Code」和「Open in Terminal」，但文件夹背景右键正常。以下 `.reg` 手动补注册表，注意将 `<user_name>` 替换为你的用户名。

```reg
Windows Registry Editor Version 5.00

; VSCode — 右键文件夹 → Open with Code
[HKEY_CURRENT_USER\Software\Classes\Directory\shell\VSCode]
@="Open with &Code"
"Icon"="C:\\Users\\<user_name>\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"

[HKEY_CURRENT_USER\Software\Classes\Directory\shell\VSCode\command]
@="\"C:\\Users\\<user_name>\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe\" \"%V\""

; Windows Terminal — 右键文件夹 → Open in Terminal
[HKEY_CURRENT_USER\Software\Classes\Directory\shell\OpenInWT]
@="Open in &Terminal"
"Icon"="C:\\Users\\<user_name>\\AppData\\Local\\Microsoft\\WindowsApps\\wt.exe"

[HKEY_CURRENT_USER\Software\Classes\Directory\shell\OpenInWT\command]
@="wt.exe -d \"%V\""
```

> 如果 VSCode 或 Windows Terminal 安装路径不同，修改 `Icon` 和 `command` 中的路径即可。合并后无需重启，刷新或重新打开文件夹窗口即生效。

## 自动恢复脚本（PowerShell）

```powershell
$codePath = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
if (-not (Test-Path $codePath)) {
    $codePath = (Get-Command code -ErrorAction SilentlyContinue).Source
}
if (-not $codePath) { Write-Error "VSCode not found" }

$key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Software\Classes\Directory\shell\VSCode", $true)
if (-not $key) {
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Software\Classes\Directory\shell\VSCode")
}
$key.SetValue("", "Open with &Code")
$key.SetValue("Icon", $codePath)
$key.Close()

$cmdKey = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Software\Classes\Directory\shell\VSCode\command")
$cmdKey.SetValue("", "`"$codePath`" `"%V`"")
$cmdKey.Close()

# Windows Terminal
$key2 = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Software\Classes\Directory\shell\OpenInWT", $true)
if (-not $key2) {
    $key2 = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Software\Classes\Directory\shell\OpenInWT")
}
$key2.SetValue("", "Open in &Terminal")
$key2.Close()

$cmdKey2 = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Software\Classes\Directory\shell\OpenInWT\command")
$cmdKey2.SetValue("", 'wt.exe -d "%V"')
$cmdKey2.Close()

Write-Output "Done. Restart Explorer or reopen folder window."
```
