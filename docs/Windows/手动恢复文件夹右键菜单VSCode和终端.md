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

## 附件：完整修复注册表

[fix-vscode-context-menu.reg](assets/fix-vscode-context-menu.reg)

用途：上面的示例只补了「文件夹右键」一个位置；这个附件补全 **4 个位置** —— 文件（`*\shell`）、文件夹（`Directory\shell`）、文件夹空白处（`Directory\Background\shell`）、盘符（`Drive\shell`），命令分别用 `%1` / `%V`，路径指向 VS Code 用户版默认安装目录。适用于新版 VS Code 在 Windows 11 上改用新式右键菜单、把经典项删掉，而新式项又因 appx 注册失效不显示的情况。

使用前把文件里所有 `<user_name>` 替换为你的 Windows 用户名，然后双击合并（写入 `HKCU`，不需要管理员权限）。合并后 Win11 默认在「显示更多选项」里可见；使用 StartAllBack 等经典菜单则直接显示。

> [!NOTE]
> 该 `.reg` 文件为 UTF-16 LE 编码（regedit 导出的默认编码）。若保存成 UTF-8，「通过 Code 打开」等中文文字会乱码。
>
> 手动补回的经典项可能在下次 VS Code 更新时再次被安装器删除：它在 Win11 判定使用新式菜单时会执行 `DeleteLegacyContextMenuRegistryKeys()`，把上面 4 个 `shell\VSCode` 键全部删掉。要长期有效，可以创建 `HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32`（空键，强制经典菜单），或重新注册当前版本的 appx 以修好新式菜单。
