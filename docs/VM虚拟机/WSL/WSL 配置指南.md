WSL 是在 Windows 下快速简单的运行 Linux 的一种方式，目前最新版本为 WSL2

## 安装 WSL

系统要求：Windows 10 x64 1903 或更高版本，内部版本为 18362 或更高版本。

参考：[官方安装教程](https://learn.microsoft.com/zh-cn/windows/wsl/install)

使用管理员权限运行命令（也可以在控制面板的 程序->启用或关闭Windows功能中开启）：
```sh
# 启用子系统
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 启用 Hyper-V
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

用命令行查找发行版：
```sh
PS C:\Windows\system32> wsl -l -o
以下是可安装的有效分发的列表。
请使用“wsl --install -d <分发>”安装。

NAME                                   FRIENDLY NAME
Ubuntu                                 Ubuntu
Debian                                 Debian GNU/Linux
kali-linux                             Kali Linux Rolling
Ubuntu-18.04                           Ubuntu 18.04 LTS
Ubuntu-20.04                           Ubuntu 20.04 LTS
Ubuntu-22.04                           Ubuntu 22.04 LTS
OracleLinux_8_5                        Oracle Linux 8.5
OracleLinux_7_9                        Oracle Linux 7.9
SUSE-Linux-Enterprise-Server-15-SP4    SUSE Linux Enterprise Server 15 SP4
openSUSE-Leap-15.4                     openSUSE Leap 15.4
openSUSE-Tumbleweed                    openSUSE Tumbleweed
```

比如我们要安装 Ubuntu 22.04 LTS，则可以输入以下命令：
```sh
wsl --install -d Ubuntu-22.04
```

查看当前安装的子系统和版本：
```sh
PS C:\Windows\system32> wsl -l -v
  NAME            STATE           VERSION
* Ubuntu-22.04    Stopped         2
```

- 安装好之后，你也许需要：[[Linux 镜像源#Ubuntu]]
- 使用文件资源管理器访问子系统路径：`\\wsl$`

## WSL 备份还原

```sh
# 停止
wsl --terminate Ubuntu-22.04

# 备份
wsl --export Ubuntu-22.04 D:\Ubuntu-22.04.tar

# 删除子系统
wsl --unregister Ubuntu-22.04

# 还原
wsl --import Ubuntu-22.04 D:\WSL D:\Ubuntu-22.04.tar
```

## WSL 从 C 盘迁移至 D 盘

参考 https://learnku.com/articles/46234

1. 下载并解压 [LxRunOffline](https://github.com/DDoSolitary/LxRunOffline) 在终端运行
2. 查看已安装的子系统：`.\LxRunOffline.exe list`
3. 查看子系统所在目录：`.\LxRunOffline.exe get-dir -n Ubuntu-20.04`
4. 新建目标目录并授权：`icacls D:\wsl\installed /grant "cnguu:(OI)(CI)(F)"`
5. 关闭正在运行的子系统：`wsl --shutdown`
6. 迁移系统：`.\LxRunOffline move -n Ubuntu-20.04 -d D:\wsl\installed\Ubuntu-20.04`
7. 如果启动出现“拒绝访问”，请在文件夹属性的安全设置里把当前用户的“完全控制”权限勾上