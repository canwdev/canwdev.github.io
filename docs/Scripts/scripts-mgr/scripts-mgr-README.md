# scripts

一堆零碎小脚本的统一入口。放在 PATH 里，按命令名直接调用，不再关心它们各自是什么语言写的。

## 加入 PATH

把本目录（例如 `D:\Projects\tools\bin\scripts` 或 `~/tools/bin/scripts`）加进系统 PATH。

**Windows（PowerShell）**

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    "D:\Projects\tools\bin\scripts;" + [Environment]::GetEnvironmentVariable("Path", "User"),
    "User"
)
```

或图形界面：`系统属性 → 环境变量 → 用户变量 → Path → 新建`。改完**重开终端**。

**macOS / Linux**

在 `~/.zshrc` 或 `~/.bashrc` 里加：

```bash
export PATH="$HOME/tools/bin/scripts:$PATH"
```

然后 `source ~/.zshrc`（或重开终端）。

**fish shell**

推荐用内置的 fish_add_path（fish 3.2+），它会自动写入 ~/.config/fish/fish_variables，无需手改配置文件：

```shell
fish_add_path ~/tools/bin/scripts
```

## Windows：生成 shim

Windows 不能直接执行 `.py` / `.mjs` / `.ps1`，需要为每个脚本生成一个同名 `.cmd` 包装（npm、pip 同款做法）。本目录的 `scripts-mgr.py` 负责这事。

```powershell
# 首次生成所有 .cmd 包装
# 新增脚本后重新生成；已存在的默认跳过
python scripts-mgr.py shim

# 生成后，可在任意位置执行 scripts-mgr
scripts-mgr ls
scripts-mgr help
scripts-mgr open
```

生成的包装与源脚本同目录，命名规则 `<脚本名>.cmd`（`convert-md2html.py` → `convert-md2html.cmd`）。`.bat` / `.cmd` 本身是 Windows 原生可执行，无需包装。

> 首次没有 `scripts-mgr.cmd` 时，用 `python scripts-mgr.py shim` 跑一次即可。

## 使用

加入 PATH 并生成 shim 后，直接按命令名调用：

```bash
convert-md2html 文档.md
convert-docx2md 报告.docx
gen-thumbs ./photos
```

参数原样透传给脚本本身。所有脚本遵循约定：成功返回 `0`，失败返回非 `0`，可被 `&&`、管道、CI 正常消费。

## 新增脚本

1. 把脚本丢进本目录（支持 `.py` / `.mjs` / `.js` / `.cjs` / `.ps1`）。
2. 加 shebang（`.py` 用 `#!/usr/bin/env python3`，`.mjs` 用 `#!/usr/bin/env node`），Unix 下再 `chmod +x`。
3. Windows：跑一次 `scripts-mgr shim` 生成包装。
4. 直接按命令名调用。