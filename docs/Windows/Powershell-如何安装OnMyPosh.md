2022.7.16 15:57

Oh My Posh 是适用于 Windows Powershell 的增强版本，类似于 Linux 下的 oh-my-zsh。官网：https://ohmyposh.dev/

## 安装：

打开Powershell（管理员），并执行以下命令：
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://ohmyposh.dev/install.ps1'))
```
安装完成后需要重启终端，才能使环境变量生效。

初始化配置：
```powershell
notepad $profile
```
打开记事本，编辑配置文件，输入以下内容：
```
oh-my-posh init pwsh --config C:\Users\user\AppData\Local\Programs\oh-my-posh\themes\negligible.omp.json | Invoke-Expression
```
其中 `negligible` 是主题名字，在这个目录下还可以看到其他主题。
若要在终端查看所有主题样式，可以输入：`Get-PoshThemes`

## 安装 Nerd Font 字体：

由于许多主题使用了字体图标，需要安装嵌入了Nerd Font的字体方可正常显示。
字体下载网站：https://www.nerdfonts.com/

推荐几个字体：
- CascadiaCode（WindowsTerminal 默认字体）
- JetBrainsMono（IDEA 默认字体）

将字体安装到系统后，还需要设置终端的字体才能使用，这里推荐几个终端软件：
- Windows Terminal
- Cmder
