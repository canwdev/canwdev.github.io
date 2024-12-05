- [中文文档](https://wyagd001.github.io/zh-cn/docs/index.htm)
- 推荐使用 VSCode 配合 AutoHotkey Plus 插件进行编辑
- [[修改狼派 A89 CIY 小键盘区按键映射（AHK脚本）]]

```ahk
; https://wyagd001.github.io/zh-cn/docs/lib/Send.htm

; 执行任何快捷键
pressKey(param){
    ; Sleep 500
    ; e.g. ^+a is ctrl+shift+a
    Send %param%
}

; 弹出一个窗口
box(myParam){
    MsgBox %myParam%
}
; myParam := "Hello, AHK!"
; box(myParam)

focusWindowByName(param) {
    SetTitleMatchMode, 2
    WinActivate, %param%
}

focusWindowByPath(param) {
    ; 通过 exe 文件路径获取窗口信息
    WinGet, hWnd, ID, % "ahk_exe " param

    ; 如果找到窗口，则激活它
    if hWnd
    {
        WinActivate, ahk_id %hWnd%
    }
    else
    {
        MsgBox, Window not found.
    }
}

; 检查是否有命令行参数
if (A_Args.Length() > 0) {
    ; 获取第一个命令行参数
    param1 := A_Args[1]
    param2 := A_Args[2]

    if (param1 == "focusByName") {
        focusWindowByName(param2)
    } else if (param1 == "focusByPath") {
        focusWindowByPath(param2)
    } else if (param1 == "key") {
        pressKey(param2)
    }
    ; box(param1)
} else {
    MsgBox Error: No params! Example: utils.exe focus Notepad
}
```