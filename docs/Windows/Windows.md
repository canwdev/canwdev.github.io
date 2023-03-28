
## 镜像下载

- [uupdump](https://uupdump.net/)
- [msdn itellyou](https://msdn.itellyou.cn/)
- [https://latest10.win/](https://latest10.win/)
- [WindowsSimplify](https://github.com/WhatTheBlock/WindowsSimplify)
- [不忘初心](https://www.pc521.net/)
- [修系统](https://www.xiuxitong.com/)

## Win11 跳过OOBE联网
在 oobe 界面按 shift+f10，弹出cmd，输入 `oobe\BypassNRO.cmd` 系统重启后就不用联网了。

## Win11 应用商店
[kinkim/InstallMicrosoftStoreOnLTSC: InstallMicrosoftStoreOnLTSC2019 (github.com)](https://github.com/kinkim/InstallMicrosoftStoreOnLTSC)

## 还原 Win11 新建文本菜单
```shell
reg.exe add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
```

## Windows 常用路径
- 家目录：`%HOMEPATH%`
- 系统盘：`%HOMEDRIVE%`
- AppData：`%$APPDATA%`
- System32：`%$System%`
- 桌面：`%$Desktop%`
- 我的文档：`%$Documents%`
- Windows：`%windir%`
- 回收站：`::{645FF040-5081-101B-9F08-00AA002F954E}`
- Linux子系统：`\\wsl$`

## Windows 开启 CompactOS
开启以节省系统占用的磁盘空间
```shell
# 查询 CompactOS
compact /compactos:query
# 关闭 CompactOS
compact /compactos:never
# 开启 CompactOS
compact /compactos:always
```

## Win10/11 端口占用
Win10/11 端口占用无法绑定，产生这个问题的原因是安装了 wsl2 或 hyper-v
参考：
- https://github.com/Fndroid/clash_for_windows_pkg/issues/671
- https://www.v2ex.com/t/835798

## 解决方案：

```sh
net stop winnat
netsh int ipv4 add excludedportrange protocol=tcp startport=7890 numberofports=1
net start winnat
```

方案2：

```sh
# 修改TCP动态端口起始端口即可，管理员运行终端命令：
netsh int ipv4 set dynamic tcp start=49152 num=16384 
# 重启后生效！
net stop winnat
net start winnat
```


## [记录 WSL 从 C 盘迁移至 D 盘 | Laravel China 社区 (learnku.com)](https://learnku.com/articles/46234)

1. 下载并解压 [LxRunOffline](https://github.com/DDoSolitary/LxRunOffline) 在终端运行
2. 查看已安装的子系统：`.\LxRunOffline.exe list`
3. 查看子系统所在目录：`.\LxRunOffline.exe get-dir -n Ubuntu-20.04`
4. 新建目标目录并授权：`icacls D:\wsl\installed /grant "cnguu:(OI)(CI)(F)"`
5. 关闭正在运行的子系统：`wsl --shutdown`
6. 迁移系统：`.\LxRunOffline move -n Ubuntu-20.04 -d D:\wsl\installed\Ubuntu-20.04`
7. 如果启动出现“拒绝访问”，请在文件夹属性的安全设置里把当前用户的“完全控制”权限勾上

## 删除 Win11 小组件
参考：[不喜欢Windows 11的小组件功能？直接命令行彻底删除 - 蓝点网 (landiannews.com)](https://www.landiannews.com/archives/95616.html)
```
1.  #打开管理员模式的命令提示符，然后执行下面的命令
2.  winget uninstall MicrosoftWindows.Client.WebExperience_cw5n1h2txyewy
3.  #该操作可能需要联网，如果报错那就再执行一次
```