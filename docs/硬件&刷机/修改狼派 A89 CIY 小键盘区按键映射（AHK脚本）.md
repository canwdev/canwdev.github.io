
修改狼派 A89 CIY 小键盘区按键映射为正常键盘配置

> 示例：完整 QWERTY 键盘：
> ![[Qwerty.svg]]
## key-remapping.ahk

保存脚本为 key-remapping.ahk
```ahk
; 以管理员权限运行，这样就能在其他高权限窗口启用按键映射了
#SingleInstance Force
SetWorkingDir %A_ScriptDir%
if not A_IsAdmin
	Run *RunAs "%A_ScriptFullPath%"

; 通用键盘映射，提升体验感 https://www.autohotkey.com/docs/v1/misc/Remap.htm
CapsLock::Ctrl

; 狼派A89 小键盘按键映射
Numpad7::PrintScreen
Numpad8::ScrollLock
Numpad9::Pause

Numpad4::Insert
Numpad5::Home
Numpad6::PgUp

Numpad1::Delete
Numpad2::End
Numpad3::PgDn

Numpad0::Del
NumpadDot::Insert
```

## 其他

1. 安装 [AHK](https://www.autohotkey.com/) [[AutoHotKey]]
2. 运行 `key-remapping_Compile.ahk` 编译脚本为 exe 程序，生成文件会存在 `C:\ProgramData\`
3. 直接运行 exe 即可。
4. 开机自启动配置：运行 `control.exe schedtasks`，手动配置开启自启动。

- 注意：如果使用远程桌面连接（mstsc），全屏窗口下可能无法传递按键映射，此时需要在远程桌面主机端也运行此脚本才能生效。
- 键盘图标可以从 C:/Windows/system32/DDORes.dll 提取

key-remapping_Compile.ahk
```.ahk
RunWait "C:\Program Files\AutoHotkey\Compiler\Ahk2Exe.exe"
 /in ".\key-remapping.ahk"
 /out "C:\ProgramData\key-remapping.exe"
 /icon ".\DDORes.dll(3073).ico"
 /base "C:\Program Files\AutoHotkey\Compiler\AutoHotkeySC.bin"
 /compress 0
```


