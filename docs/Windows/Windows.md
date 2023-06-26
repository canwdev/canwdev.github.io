
- [[Windows 脚本 + 常用命令]]
- [[Windows 使用VHD镜像无损备份恢复系统]]
- [[Windows UEFI BCD 引导修复]]
- [[Windows 注册表]]

## 镜像下载

- [uupdump](https://uupdump.net/)
- [msdn itellyou](https://msdn.itellyou.cn/)
- [https://latest10.win/](https://latest10.win/)
- [WindowsSimplify](https://github.com/WhatTheBlock/WindowsSimplify)
- [系统 - 果核剥壳](https://www.ghxi.com/category/all/system)
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

方案1：
```sh
net stop winnat
netsh int ipv4 add excludedportrange protocol=tcp startport=7890 numberofports=1
net start winnat
```

方案2（推荐）：
```sh
# 修改TCP动态端口起始端口即可，管理员运行终端命令：
netsh int ipv4 set dynamic tcp start=49152 num=16384 
# 重启服务后立即生效！
net stop winnat
net start winnat
```

## 删除 Win11 小组件

参考 [不喜欢Windows 11的小组件功能？直接命令行彻底删除 - 蓝点网 (landiannews.com)](https://www.landiannews.com/archives/95616.html)

1.  打开管理员模式的命令提示符，然后执行下面的命令
2.  `winget uninstall MicrosoftWindows.Client.WebExperience_cw5n1h2txyewy`
3.  该操作可能需要联网，如果报错那就再执行一次
4. 或可以直接使用 Dism++ 删除 Appx 包


## 消除【这些文件可能对你的计算机有害】对话框

从网络复制文件时，消除“这些文件可能对你的计算机有害”对话框

如果你要访问的域是 192.168.1.1，可以按照以下步骤在 Internet 属性中添加信任：

1. 打开 Internet Explorer 浏览器，在菜单栏上点击“工具”选项，然后选择“Internet 选项”。
2. 在 Internet 属性窗口中，切换到“安全”选项卡。
3. 选中“本地 Intranet”区域，并点击“站点”按钮。
4. 在“本地 Intranet”窗口中，点击“高级”按钮。
5. 在“向此区域中添加此站点”文本框中输入 IP 地址：192.168.1.1，并点击“添加”按钮。
6. 确认 IP 地址已被添加到“网站列表”中，然后点击“关闭”按钮。
8. 在“安全”选项卡中，选中“本地 Intranet”，点击“默认级别”按钮。
9. 将该区域的安全级别调整为“低”。
10. 点击“确定”按钮，关闭所有窗口。

现在你可以重新访问 192.168.0.1，如果还是有弹窗可以尝试重启。

---

- [Win11 资源管理器（文件夹）出现的菜单栏怎么隐藏？ | 竹山一叶 (zsyyblog.com)](https://zsyyblog.com/a2ad5b83.html)