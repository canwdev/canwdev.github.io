# PowerShell (pwsh) 笔记

## pwsh 与 Windows PowerShell 区别

|     | Windows PowerShell | pwsh (PowerShell 7+)      |
| --- | ------------------ | ------------------------- |
| 平台  | 仅 Windows          | 跨平台 (Windows/macOS/Linux) |
| 框架  | .NET Framework     | .NET (Core)               |
| 版本  | 最高 5.1             | 持续更新 (7.x)                |
| 开源  | 否                  | 是                         |

大部分命令兼容，但旧模块/功能仅限 Windows PowerShell 5.1。

## 安装 pwsh

```powershell
# 推荐：winget
winget install Microsoft.PowerShell

# 或从 GitHub 下载 MSI
# https://github.com/PowerShell/PowerShell/releases
```

安装后终端输入 `pwsh` 启动。

## 设为默认终端

**推荐：Windows Terminal 设置**
1. 打开 Windows Terminal → Ctrl+, → 启动
2. **默认配置文件** → 选择 **PowerShell 7**
3. **默认终端应用程序** → 选择 **Windows Terminal**

**VS Code 中设为默认**
- `Ctrl+Shift+P` → `Terminal: Select Default Profile` → 选择 **PowerShell 7**

## Coreutils

**GNU Coreutils** — Linux/Unix 系统基本命令行工具集，包含：
- 文件操作：`ls`, `cp`, `mv`, `rm`, `mkdir`, `touch`
- 文本处理：`cat`, `echo`, `head`, `tail`, `sort`, `wc`
- 其他：`chmod`, `chown`, `date`, `sleep`, `whoami`

Windows 替代方案：Git Bash、WSL、Scoop (`scoop install coreutils`)

## microsoft/coreutils

微软 2026 年发布的项目，让 Unix 命令原生运行在 Windows 上。

- **基于** Rust 重写的 [uutils/coreutils](https://github.com/uutils/coreutils)
- **安装**: `winget install Microsoft.Coreutils`
- **内容**: 75+ GNU 命令 + findutils (`find`, `xargs`) + `grep`
- **注意**: 与 PowerShell 别名有冲突 (`cat`, `cp`, `ls`, `rm` 等)，安装时会询问是否修改 `$PROFILE`

## PSReadLine 预测提示（类似 fish 自动补全）

PowerShell 7.4+ 默认开启预测提示（`PredictionSource = History`），从历史记录显示建议，但默认是 **列表视图**。

**切换为 fish 风格的行内提示：**
```powershell
Set-PSReadLineOption -PredictionViewStyle Inline
```

**同时启用列表 + 行内：**
```powershell
Set-PSReadLineOption -PredictionViewStyle Inline, ListView
```

### PowerShell 5.1

默认 **关闭**，需手动启用：
```powershell
Set-PSReadLineOption -HistorySearchCursorMovesToEnd
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle Inline
```

建议先升级 PSReadLine（5.1 预装版本较旧）：
```powershell
Install-Module PSReadLine -Force
```

将上述命令添加到 `$PROFILE` 即可持久化。
