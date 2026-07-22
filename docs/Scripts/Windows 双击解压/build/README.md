# bat2exe

把 `.bat` 打包成带可选图标的 `.exe`（调用系统自带 `csc`，无需额外安装）。

在本目录（`build`）下执行下列命令。

## 用法

```powershell
# 基本：exe 生成在源 bat 同目录（同名 .exe）
.\bat2exe.ps1 -bat ..\SmartExtract7z.bat

# 指定图标（支持 .ico / .exe / .dll，后两者会提取关联图标）
.\bat2exe.ps1 -bat ..\SmartExtract7z.bat -icon "C:\Program Files\7-Zip\7zFM.exe"

# 指定输出路径（可写到任意位置）
.\bat2exe.ps1 -bat ..\SmartExtract7z.bat -icon "C:\Program Files\7-Zip\7zFM.exe" -out ..\SmartExtract7z.exe

# 保留控制台窗口（默认无窗口）
.\bat2exe.ps1 -bat ..\foo.bat -console
```

位置参数也可：

```powershell
.\bat2exe.ps1 ..\SmartExtract7z.bat "C:\Program Files\7-Zip\7zFM.exe"
```

## 参数

| 参数 | 说明 |
|------|------|
| `-bat` | 必填，源 bat 路径 |
| `-icon` | 可选，图标来源（`.ico` / `.exe` / `.dll`） |
| `-out` | 可选，输出 exe；**默认与源 bat 同目录、同名**（不是“当前工作目录”） |
| `-console` | 可选，显示控制台；默认 `winexe` 无黑框 |

## 输出位置

- **未指定 `-out`**：exe 写在源 bat 所在目录（例如 `-bat ..\SmartExtract7z.bat` → 上级目录的 `SmartExtract7z.exe`）
- **指定了 `-out`**：按你给的路径输出

## 说明

- exe 会嵌入 bat 原文，运行时写出临时 bat 再执行，并转发命令行参数
- 改 bat 后需重新执行本脚本生成 exe
- 适合作为文件默认打开程序（可保留自定义图标）
